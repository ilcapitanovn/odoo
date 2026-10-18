# -*- coding: utf-8 -*-
import re
import unicodedata
from collections import Counter, defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

PARAM_MAX = 'freight_mto_auto_subproducts.suggest_max'
DEFAULT_MAX = 20
HISTORY_BOOKINGS = 50       # most recent bookings analysed
HISTORY_LINES = 300         # most recent PO lines of the main product read
HISTORY_PRESELECT = 0.5     # tick by default when seen in >= 50% of bookings


def name_tokens(name):
    """Upper-case, accent-free alphanumeric tokens (>= 2 chars) of a name."""
    text = unicodedata.normalize('NFD', name or '')
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('Đ', 'D').replace('đ', 'd').upper()
    return {t for t in re.findall(r'[A-Z0-9]+', text) if len(t) >= 2}


def similarity(name_a, name_b):
    a, b = name_tokens(name_a), name_tokens(name_b)
    return len(a & b) / float(len(a | b)) if (a and b) else 0.0


def split_origin(origin):
    return [t for t in re.split(r'[,;\s]+', origin or '') if t]


class MtoSubproductSuggestWizard(models.TransientModel):
    _name = 'mto.subproduct.suggest.wizard'
    _description = 'Suggest MTO Sub-Products'

    template_id = fields.Many2one(
        'product.template', string='Main Product', required=True,
        readonly=True, ondelete='cascade')
    source_template_id = fields.Many2one(
        'product.template', string='Copy from similar product',
        domain="[('mto_subproduct_ids', '!=', False), ('id', '!=', template_id)]",
        help="Sub-products of this product are suggested when PO history "
             "does not fill all free slots. Change it and click 'Reload'.")
    history_info = fields.Char(string='PO history', readonly=True)
    existing_count = fields.Integer(compute='_compute_capacity')
    max_count = fields.Integer(compute='_compute_capacity')
    free_slots = fields.Integer(compute='_compute_capacity')
    line_ids = fields.One2many(
        'mto.subproduct.suggest.wizard.line', 'wizard_id', string='Suggestions')

    # ------------------------------------------------------------------
    # Capacity
    # ------------------------------------------------------------------
    @api.model
    def _get_max(self):
        try:
            return int(self.env['ir.config_parameter'].sudo().get_param(
                PARAM_MAX, DEFAULT_MAX))
        except ValueError:
            return DEFAULT_MAX

    def _existing_configs(self):
        return self.env['product.template.mto.subproduct'].with_context(
            active_test=False).search([('template_id', '=', self.template_id.id)])

    @api.depends('template_id')
    def _compute_capacity(self):
        max_count = self._get_max()
        for wiz in self:
            existing = len(wiz._existing_configs()) if wiz.template_id else 0
            wiz.existing_count = existing
            wiz.max_count = max_count
            wiz.free_slots = max(max_count - existing, 0)

    # ------------------------------------------------------------------
    # Eligibility
    # ------------------------------------------------------------------
    def _main_template_ids(self):
        groups = self.env['product.template.mto.subproduct'].sudo().with_context(
            active_test=False).read_group([], ['template_id'], ['template_id'])
        return {g['template_id'][0] for g in groups}

    def _eligible(self, products):
        """Purchasable, active, not the main product and not a main product
        itself (nested expansion is not supported)."""
        main_ids = self._main_template_ids()
        return products.filtered(
            lambda p: p.active and p.purchase_ok
            and p.product_tmpl_id != self.template_id
            and p.product_tmpl_id.id not in main_ids)

    def _excluded_product_ids(self):
        return set(self._existing_configs().mapped('sub_product_id').ids)

    # ------------------------------------------------------------------
    # Source 1: PO history
    # ------------------------------------------------------------------
    def _history_lines(self, excluded_ids):
        """Products bought together with the main product on past bookings.

        A booking = a source document (SO number) found in the origin of the
        POs. All confirmed POs sharing that origin belong to the booking, even
        when they are addressed to different vendors.
        Returns (list of line vals, info text).
        """
        self.ensure_one()
        tmpl = self.template_id
        cids = self.env.companies.ids
        Line = self.env['purchase.order.line'].sudo()
        a_lines = Line.search([
            ('product_id.product_tmpl_id', '=', tmpl.id),
            ('order_id.state', 'in', ('purchase', 'done')),
            ('company_id', 'in', cids),
        ], order='id desc', limit=HISTORY_LINES)

        bookings = {}   # origin token -> {'a_qty', 'partner'}
        for line in a_lines:
            qty = line.product_uom._compute_quantity(
                line.product_qty, line.product_id.uom_id)
            for token in split_origin(line.order_id.origin):
                if token not in bookings and len(bookings) >= HISTORY_BOOKINGS:
                    continue
                bk = bookings.setdefault(
                    token, {'a_qty': 0.0, 'partner': line.order_id.partner_id.id})
                bk['a_qty'] += qty
        if not bookings:
            return [], _("No purchase history found for this product.")

        domain = expression.AND([
            expression.OR([[('origin', 'ilike', t)] for t in bookings]),
            [('state', 'in', ('purchase', 'done')), ('company_id', 'in', cids)],
        ])
        pos = self.env['purchase.order'].sudo().search(domain)

        # product id -> booking token -> {'qty', 'vendors'}
        per_product = defaultdict(lambda: defaultdict(
            lambda: {'qty': 0.0, 'vendors': Counter()}))
        for po in pos:
            tokens = set(split_origin(po.origin)) & set(bookings)
            if not tokens:
                continue
            for line in po.order_line:
                prod = line.product_id
                if (line.display_type or not prod or line.is_mto_auto_line
                        or prod.product_tmpl_id == tmpl
                        or prod.id in excluded_ids):
                    continue
                qty = line.product_uom._compute_quantity(
                    line.product_qty, prod.uom_po_id)
                for token in tokens:
                    # same vendor as the main PO -> no vendor override needed
                    vendor = (False if po.partner_id.id == bookings[token]['partner']
                              else po.partner_id.id)
                    data = per_product[prod.id][token]
                    data['qty'] += qty
                    data['vendors'][vendor] += 1

        rows = []
        for pid, by_booking in per_product.items():
            ratios, vendors = [], Counter()
            for token, data in by_booking.items():
                a_qty = bookings[token]['a_qty']
                ratios.append(data['qty'] / a_qty if a_qty else data['qty'])
                vendors.update(data['vendors'])
            rows.append({
                'pid': pid, 'count': len(by_booking),
                'qty': round(sum(ratios) / len(ratios), 3) or 1.0,
                'vendor': vendors.most_common(1)[0][0],
            })
        rows.sort(key=lambda r: (-r['count'], r['pid']))

        products = self._eligible(
            self.env['product.product'].browse([r['pid'] for r in rows]))
        total = len(bookings)
        vals_list = []
        for row in rows:
            if row['pid'] not in products.ids:
                continue
            vals_list.append({
                'source': 'history',
                'sub_product_id': row['pid'],
                'vendor_id': row['vendor'] or False,
                'qty': row['qty'],
                'selected': row['count'] / float(total) >= HISTORY_PRESELECT,
                'evidence': _("Bought in %(n)s of %(t)s past bookings") % {
                    'n': row['count'], 't': total},
            })
        info = _("Based on %s past booking(s) of this product.") % total
        return vals_list, info

    # ------------------------------------------------------------------
    # Source 2: copy from a similar product
    # ------------------------------------------------------------------
    def _best_similar_template(self):
        Config = self.env['product.template.mto.subproduct'].sudo()
        groups = Config.read_group(
            [('active', '=', True), ('template_id', '!=', self.template_id.id)],
            ['template_id'], ['template_id'])
        templates = self.env['product.template'].search(
            [('id', 'in', [g['template_id'][0] for g in groups])])
        best, best_score = self.env['product.template'], 0.0
        for tmpl in templates:
            score = similarity(self.template_id.name, tmpl.name)
            if score > best_score:
                best, best_score = tmpl, score
        return best, best_score

    def _similar_lines(self, source, used_ids, limit):
        self.ensure_one()
        score = similarity(self.template_id.name, source.name)
        configs = source.mto_subproduct_ids.filtered('active').sorted(
            lambda c: (c.sequence, c.id))
        eligible_ids = set(self._eligible(configs.mapped('sub_product_id')).ids)
        vals_list = []
        for cfg in configs:
            pid = cfg.sub_product_id.id
            if pid in used_ids or pid not in eligible_ids:
                continue
            if len(vals_list) >= limit:
                break
            used_ids = used_ids | {pid}
            vals_list.append({
                'source': 'similar',
                'sub_product_id': pid,
                'vendor_id': cfg.vendor_id.id,
                'qty': cfg.qty,
                'note': cfg.note,
                'selected': True,
                'evidence': _("Copied from %(p)s (name match %(s)d%%)") % {
                    'p': source.display_name, 's': round(score * 100)},
            })
        return vals_list

    # ------------------------------------------------------------------
    # Build / reload
    # ------------------------------------------------------------------
    def _populate(self):
        self.ensure_one()
        excluded = self._excluded_product_ids()
        slots = self._existing_slots()
        history_vals, info = self._history_lines(excluded)
        vals_list = history_vals[:slots]
        source, _score = self._best_similar_template()
        remaining = slots - len(vals_list)
        if source and remaining > 0:
            used = excluded | {v['sub_product_id'] for v in vals_list}
            vals_list += self._similar_lines(source, used, remaining)
        for index, vals in enumerate(vals_list, start=1):
            vals['sequence'] = index * 10
        self.write({
            'source_template_id': source.id or False,
            'history_info': info,
            'line_ids': [(0, 0, v) for v in vals_list],
        })

    def _existing_slots(self):
        return max(self._get_max() - len(self._existing_configs()), 0)

    def action_reload_similar(self):
        """Replace the 'similar product' suggestions by those of the product
        chosen in 'Copy from similar product'."""
        self.ensure_one()
        self.line_ids.filtered(lambda l: l.source == 'similar').unlink()
        if self.source_template_id:
            used = self._excluded_product_ids() | set(
                self.line_ids.mapped('sub_product_id').ids)
            slots = self._existing_slots() - len(self.line_ids)
            vals_list = self._similar_lines(self.source_template_id, used, slots) \
                if slots > 0 else []
            start = max(self.line_ids.mapped('sequence') or [0])
            for index, vals in enumerate(vals_list, start=1):
                vals['sequence'] = start + index * 10
            self.write({'line_ids': [(0, 0, v) for v in vals_list]})
        return self._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Suggest Sub-Products"),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ------------------------------------------------------------------
    # Confirm
    # ------------------------------------------------------------------
    def action_confirm(self):
        self.ensure_one()
        lines = self.line_ids.filtered('selected')
        if not lines:
            raise UserError(_("Tick at least one suggested sub-product."))
        existing = self._existing_configs()
        max_count = self._get_max()
        if len(existing) + len(lines) > max_count:
            raise UserError(_(
                "A product can have at most %(max)s sub-products. It already has "
                "%(have)s and you selected %(new)s.") % {
                    'max': max_count, 'have': len(existing), 'new': len(lines)})
        already = set(existing.mapped('sub_product_id').ids)
        sequence = max(existing.mapped('sequence') or [0])
        vals_list = []
        for line in lines.sorted(lambda l: (l.sequence, l.id)):
            if line.sub_product_id.id in already:
                continue
            sequence += 10
            vals_list.append({
                'template_id': self.template_id.id,
                'sequence': sequence,
                'sub_product_id': line.sub_product_id.id,
                'vendor_id': line.vendor_id.id,
                'qty': line.qty,
                'note': line.note,
            })
        self.env['product.template.mto.subproduct'].create(vals_list)
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class MtoSubproductSuggestWizardLine(models.TransientModel):
    _name = 'mto.subproduct.suggest.wizard.line'
    _description = 'Suggested MTO Sub-Product'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'mto.subproduct.suggest.wizard', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    selected = fields.Boolean(string='Add', default=True)
    source = fields.Selection(
        [('history', 'PO history'), ('similar', 'Similar product')],
        required=True)
    sub_product_id = fields.Many2one(
        'product.product', string='Sub-Product', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    qty = fields.Float(
        string='Default Qty', default=1.0, digits='Product Unit of Measure')
    uom_id = fields.Many2one(
        related='sub_product_id.uom_po_id', string='Unit of Measure',
        readonly=True)
    note = fields.Char(string='Notes')
    evidence = fields.Char(string='Why suggested', readonly=True)
