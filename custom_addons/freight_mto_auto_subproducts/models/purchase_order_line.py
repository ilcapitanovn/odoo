# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_mto_auto_line = fields.Boolean(
        string='Auto Sub-Product', readonly=True, copy=False,
        help="Line generated automatically from the MTO sub-products "
             "configuration of the main product.")
    mto_parent_line_id = fields.Many2one(
        'purchase.order.line', string='Main PO Line', readonly=True,
        copy=False, ondelete='set null', index=True)
    mto_subproduct_id = fields.Many2one(
        'product.template.mto.subproduct', string='MTO Sub-Product Config',
        readonly=True, copy=False, ondelete='set null')

    # ------------------------------------------------------------------
    # Expansion
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if self.env.context.get('mto_expand_subproducts'):
            to_expand = lines.filtered(
                lambda l: not l.display_type
                and not l.is_mto_auto_line
                and l.product_id
                and l.order_id.state == 'draft'
                # skip min/max reordering rules: only sales-driven MTO
                and not l.orderpoint_id)
            to_expand._mto_expand_subproducts()
        return lines

    def write(self, vals):
        track_qty = (self.env.context.get('mto_expand_subproducts')
                     and 'product_qty' in vals)
        old_qty = {l.id: l.product_qty for l in self} if track_qty else {}
        res = super().write(vals)
        if track_qty:
            self._mto_adjust_children(old_qty)
        return res

    def _mto_expand_subproducts(self):
        """Create the sub-product lines for the lines in ``self``."""
        vals_list = []
        for line in self:
            tmpl = line.product_id.product_tmpl_id.sudo()
            configs = tmpl.mto_subproduct_ids.filtered('active').sorted(
                lambda c: (c.sequence, c.id))
            if not configs:
                continue
            base_qty = line.product_uom._compute_quantity(
                line.product_qty, line.product_id.uom_id)
            main_po = line.order_id
            for cfg in configs:
                if cfg.vendor_id and cfg.vendor_id != main_po.partner_id:
                    po = main_po._mto_get_or_create_vendor_po(cfg.vendor_id)
                else:
                    po = main_po
                vals_list.append(
                    line._mto_prepare_sub_line_vals(cfg, po, base_qty))
        if vals_list:
            self.env['purchase.order.line'].sudo().with_context(
                mto_expand_subproducts=False).create(vals_list)

    def _mto_prepare_sub_line_vals(self, cfg, po, base_qty):
        """Values for the PO line of sub-product ``cfg`` on order ``po``."""
        self.ensure_one()
        sub = cfg.sub_product_id
        company = po.company_id
        partner = po.partner_id
        qty = cfg.qty * base_qty                      # in sub.uom_po_id
        date = po.date_order.date() if po.date_order else fields.Date.today()

        seller = sub.with_company(company)._select_seller(
            partner_id=partner, quantity=qty, date=date, uom_id=sub.uom_po_id)

        taxes = sub.supplier_taxes_id.filtered(lambda t: t.company_id == company)
        if po.fiscal_position_id:
            taxes = po.fiscal_position_id.map_tax(taxes)
        price_unit = 0.0
        if seller:
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                seller.price, sub.supplier_taxes_id, taxes, company)
            if po.currency_id and seller.currency_id != po.currency_id:
                price_unit = seller.currency_id._convert(
                    price_unit, po.currency_id, company,
                    po.date_order or fields.Date.today(), round=False)

        sub_lang = sub.with_context(lang=partner.lang, partner_id=partner.id)
        name = sub_lang.display_name
        if sub_lang.description_purchase:
            name += '\n' + sub_lang.description_purchase
        if cfg.note:
            name += '\n' + cfg.note

        return {
            'order_id': po.id,
            'product_id': sub.id,
            'name': name,
            'product_qty': qty,
            'product_uom': sub.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': self.date_planned or fields.Datetime.now(),
            'taxes_id': [(6, 0, taxes.ids)],
            'is_mto_auto_line': True,
            'mto_parent_line_id': self.id,
            'mto_subproduct_id': cfg.id,
        }

    def _mto_adjust_children(self, old_qty):
        """The Buy flow merged extra demand into an existing main line
        (qty increased): add the matching amount to its sub-lines."""
        children = self.env['purchase.order.line'].sudo().search(
            [('mto_parent_line_id', 'in', self.ids)])
        for line in self:
            delta = line.product_qty - old_qty.get(line.id, line.product_qty)
            if not delta:
                continue
            delta_base = line.product_uom._compute_quantity(
                delta, line.product_id.uom_id)
            for child in children.filtered(lambda c: c.mto_parent_line_id == line):
                cfg = child.mto_subproduct_id
                if not cfg:
                    continue
                new_qty = child.product_qty + cfg.qty * delta_base
                child.with_context(mto_expand_subproducts=False).write(
                    {'product_qty': max(new_qty, 0.0)})
