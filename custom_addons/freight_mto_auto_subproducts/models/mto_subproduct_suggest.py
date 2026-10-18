# -*- coding: utf-8 -*-
import re
import unicodedata
from collections import Counter, defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

PARAM_MAX = 'freight_mto_auto_subproducts.suggest_max'
DEFAULT_MAX = 20
POOL_LIMIT = 2000           # similarity: max candidate products scored
VENDOR_BONUS = 0.25         # similarity: bonus for a favoured vendor
HISTORY_BOOKINGS = 50       # history: most recent bookings analysed
HISTORY_LINES = 300         # history: most recent PO lines of the main product
HISTORY_PRESELECT = 0.5     # history: tick when seen in >= 50% of bookings


def normalize(text):
    """Upper-case, accent-free text (Vietnamese friendly)."""
    text = unicodedata.normalize('NFD', text or '')
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.replace('Đ', 'D').replace('đ', 'd').upper()


def token_list(text):
    """Ordered, distinct [(raw, normalized)] tokens (>= 2 chars)."""
    out, seen = [], set()
    for raw in re.findall(r'\w+', text or '', re.UNICODE):
        norm = re.sub(r'[^A-Z0-9]', '', normalize(raw))
        if len(norm) < 2 or norm in seen:
            continue
        seen.add(norm)
        out.append((raw, norm))
    return out


def split_origin(origin):
    return [t for t in re.split(r'[,;\s]+', origin or '') if t]


class MtoSubproductSuggestWizard(models.TransientModel):
    _name = 'mto.subproduct.suggest.wizard'
    _description = 'Suggest MTO Sub-Products'

    template_id = fields.Many2one(
        'product.template', string='Main Product', required=True,
        readonly=True, ondelete='cascade')
    mode = fields.Selection(
        [('similar', 'Product name and vendor name similarity'),
         ('history', 'Purchase history')],
        string='Suggest by', default='similar', required=True)
    # --- similarity mode
    keywords = fields.Char(
        help="Words searched in the names of all purchasable products and of "
             "their vendors (accent-insensitive, partial words allowed, e.g. "
             "'JJ' finds 'SJJ').")
    vendor_ids = fields.Many2many(
        'res.partner', 'mto_subproduct_suggest_wizard_vendor_rel',
        'wizard_id', 'partner_id', string='Favoured vendors',
        help="Products bought from these vendors rank higher. Defaults to the "
             "vendors of the main product.")
    ignore_word_ids = fields.Many2many(
        'mto.subproduct.ignore.word', 'mto_subproduct_suggest_wizard_ignore_rel',
        'wizard_id', 'word_id', string='Ignored words',
        help="Skipped in the similarity search. Words added here are saved in "
             "the global list (Purchase > Configuration > Sub-Product Ignore "
             "Words); removing a tag only applies to this search.")
    info = fields.Char(string='Search result', readonly=True)
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

    def _existing_slots(self):
        return max(self._get_max() - len(self._existing_configs()), 0)

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
    # Ignore words
    # ------------------------------------------------------------------
    def _ignored_tokens(self):
        """Every word of every ignore entry (normalized)."""
        return {norm for word in self.ignore_word_ids
                for _raw, norm in token_list(word.name)}

    def _ignored_phrases(self):
        """Multi-word entries: a product whose name contains the whole phrase
        is a 'main-like' product and is not suggested."""
        phrases = []
        for word in self.ignore_word_ids:
            tokens = [norm for _raw, norm in token_list(word.name)]
            if len(tokens) >= 2:
                phrases.append(' '.join(tokens))
        return phrases

    def _default_keywords(self):
        ignored = self._ignored_tokens()
        return ' '.join(raw for raw, norm in token_list(self.template_id.name)
                        if norm not in ignored)

    # ------------------------------------------------------------------
    # Mode 1: product name and vendor name similarity
    # ------------------------------------------------------------------
    def _similar_lines(self):
        """Score every purchasable product against the keywords.

        A keyword matches when it is contained in the product name or in the
        name of one of its vendors. Score = matched keywords / keywords that
        matched at least one product, plus a bonus when the product is bought
        from a favoured vendor. Ignored words are removed from the keywords
        and products containing an ignored phrase are skipped.
        """
        self.ensure_one()
        tmpl = self.template_id
        slots = self._existing_slots()
        if slots <= 0:
            return [], _("No free slot: the product already has %s sub-products."
                         ) % self._get_max()
        ignored = self._ignored_tokens()
        pairs = [(raw, norm) for raw, norm in token_list(self.keywords)
                 if norm not in ignored]
        if not pairs:
            return [], _("No keyword left (ignored words removed). Enter keywords "
                         "and click Reload.")

        domain_or = []
        for raw, _norm in pairs:
            domain_or.append([('name', 'ilike', raw)])
            domain_or.append([('product_tmpl_id.seller_ids.name', 'ilike', raw)])
        domain = expression.AND([
            [('purchase_ok', '=', True),
             ('product_tmpl_id', '!=', tmpl.id),
             ('id', 'not in', list(self._excluded_product_ids()))],
            expression.OR(domain_or),
        ])
        pool = self._eligible(
            self.env['product.product'].search(domain, limit=POOL_LIMIT))

        phrases = self._ignored_phrases()
        today = fields.Date.context_today(self)

        def valid_sellers(template):
            return template.seller_ids.filtered(
                lambda s: not s.date_end or s.date_end >= today)

        favoured = set(self.vendor_ids.ids)
        main_vendor = valid_sellers(tmpl)[:1].name

        rows = []
        for prod in pool:
            if phrases:
                name_tokens = ' '.join(n for _r, n in token_list(prod.name))
                if any(ph in name_tokens for ph in phrases):
                    continue
            hay = normalize(prod.name)
            sellers = valid_sellers(prod.product_tmpl_id)
            seller_hay = {s.id: normalize(s.name.name) for s in sellers}
            by_name, by_vendor = [], []
            for _raw, norm in pairs:
                if norm in hay:
                    by_name.append(norm)
                elif any(norm in h for h in seller_hay.values()):
                    by_vendor.append(norm)
            matched = by_name + by_vendor
            if not matched:
                continue
            fav_sellers = sellers.filtered(lambda s: s.name.id in favoured)
            named = sellers.filtered(lambda s: any(
                norm in seller_hay[s.id] for _raw, norm in pairs))
            chosen = (fav_sellers[:1] or named[:1] or sellers[:1])
            partner = chosen.name
            rows.append({
                'prod': prod, 'matched': matched,
                'by_name': by_name, 'by_vendor': by_vendor,
                'favoured': bool(fav_sellers),
                # same vendor as the main product -> no vendor override needed
                'vendor_id': (partner.id if partner and partner != main_vendor
                              else False),
            })

        effective = {t for row in rows for t in row['matched']}
        for row in rows:
            score = len(row['matched']) / float(len(effective))
            if row['favoured']:
                score = min(1.0, score + VENDOR_BONUS)
            row['score'] = score
        rows.sort(key=lambda r: (-r['score'], -len(r['matched']), r['prod'].name or ''))

        vals_list = []
        for row in rows[:slots]:
            parts = []
            if row['by_name']:
                parts.append(_("Name: %s") % ', '.join(row['by_name']))
            if row['by_vendor']:
                parts.append(_("Vendor: %s") % ', '.join(row['by_vendor']))
            if row['favoured']:
                parts.append(_("Favoured vendor"))
            vals_list.append({
                'sub_product_id': row['prod'].id,
                'vendor_id': row['vendor_id'],
                'qty': 1.0,
                'selected': len(row['matched']) >= 2 or row['favoured'],
                'evidence': "%s (%d%%)" % (' · '.join(parts), round(row['score'] * 100)),
            })
        unmatched = [raw for raw, norm in pairs if norm not in effective]
        info = _("%(n)s product(s) match; showing the best %(s)s.") % {
            'n': len(rows), 's': len(vals_list)}
        if unmatched:
            info += " " + _("Keywords with no match: %s.") % ', '.join(unmatched)
        return vals_list, info

    # ------------------------------------------------------------------
    # Mode 2: purchase history
    # ------------------------------------------------------------------
    def _history_lines(self):
        """Products bought together with the main product on past bookings.

        A booking = a source document (SO number) found in the origin of the
        POs. All confirmed POs sharing that origin belong to the booking, even
        when addressed to different vendors.
        """
        self.ensure_one()
        tmpl = self.template_id
        slots = self._existing_slots()
        if slots <= 0:
            return [], _("No free slot: the product already has %s sub-products."
                         ) % self._get_max()
        excluded_ids = self._excluded_product_ids()
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
            if row['pid'] not in products.ids or len(vals_list) >= slots:
                continue
            vals_list.append({
                'sub_product_id': row['pid'],
                'vendor_id': row['vendor'] or False,
                'qty': row['qty'],
                'selected': row['count'] / float(total) >= HISTORY_PRESELECT,
                'evidence': _("Bought in %(n)s of %(t)s past bookings") % {
                    'n': row['count'], 't': total},
            })
        info = _("Based on %(t)s past booking(s) of this product; showing %(s)s.") % {
            't': total, 's': len(vals_list)}
        return vals_list, info

    # ------------------------------------------------------------------
    # Build / reload
    # ------------------------------------------------------------------
    def _populate(self):
        """Initial state when the wizard opens: similarity mode."""
        self.ensure_one()
        words = self.env['mto.subproduct.ignore.word'].search([])
        self.write({'ignore_word_ids': [(6, 0, words.ids)]})
        vendors = self.template_id.seller_ids.mapped('name')
        self.write({
            'mode': 'similar',
            'keywords': self._default_keywords(),
            'vendor_ids': [(6, 0, vendors.ids)],
        })
        self._run_search()

    def _run_search(self):
        self.ensure_one()
        self.line_ids.unlink()
        if self.mode == 'history':
            vals_list, info = self._history_lines()
        else:
            vals_list, info = self._similar_lines()
        for index, vals in enumerate(vals_list, start=1):
            vals['sequence'] = index * 10
        self.write({
            'info': info,
            'line_ids': [(0, 0, v) for v in vals_list],
        })

    def action_reload(self):
        """Rebuild the suggestions for the selected mode / keywords."""
        self.ensure_one()
        self._run_search()
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
