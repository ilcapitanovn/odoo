# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplateMtoSubproduct(models.Model):
    _name = 'product.template.mto.subproduct'
    _description = 'MTO Auto PO Sub-Product'
    _order = 'template_id, sequence, id'

    template_id = fields.Many2one(
        'product.template', string='Main Product', required=True,
        ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    sub_product_id = fields.Many2one(
        'product.product', string='Sub-Product', required=True,
        domain=[('purchase_ok', '=', True)], ondelete='restrict')
    vendor_id = fields.Many2one(
        'res.partner', string='Vendor',
        help="Optional. If set (and different from the vendor of the main PO), "
             "the sub-product is added to a separate draft PO for this vendor. "
             "If empty, it is added to the same PO as the main product.")
    qty = fields.Float(
        string='Default Qty', default=1.0,
        digits='Product Unit of Measure',
        help="Quantity of sub-product (in its purchase unit of measure) per "
             "1 unit of the main product.")
    standard_price_usd = fields.Float(
        string="Cost (USD)",
        digits='Product Price', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the next unit that will leave the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")
    standard_price_vnd = fields.Float(
        string="Cost (VND)",
        digits='Product Price', groups="base.group_user")
    uom_id = fields.Many2one(
        related='sub_product_id.uom_po_id', string='Unit of Measure',
        readonly=True)
    note = fields.Char(
        string='Notes', help="Appended to the description of the generated PO line.")
    currency_id = fields.Many2one(
        related='template_id.currency_id', store=True, readonly=True)
    company_id = fields.Many2one(
        related='template_id.company_id', store=True, readonly=True)

    @api.constrains('qty')
    def _check_qty(self):
        for rec in self:
            if rec.qty < 0:
                raise ValidationError(_("Default Qty must be strictly positive."))

    @api.constrains('sub_product_id', 'template_id')
    def _check_sub_product(self):
        for rec in self:
            sub_tmpl = rec.sub_product_id.product_tmpl_id
            if sub_tmpl == rec.template_id:
                raise ValidationError(
                    _("A product cannot be its own sub-product (%s).")
                    % rec.template_id.display_name)
            # No nesting (avoid loops): a sub-product cannot have sub-products...
            if sub_tmpl.sudo().with_context(active_test=False).mto_subproduct_ids:
                raise ValidationError(
                    _("'%s' has its own MTO sub-products, so it cannot be used as a "
                      "sub-product of '%s'. Nested expansion is not supported.")
                    % (sub_tmpl.display_name, rec.template_id.display_name))
            # ... and a product used as sub-product elsewhere cannot get sub-products.
            used_as_sub = self.sudo().with_context(active_test=False).search_count([
                ('sub_product_id.product_tmpl_id', '=', rec.template_id.id)])
            if used_as_sub:
                raise ValidationError(
                    _("'%s' is already used as a sub-product of another product, so "
                      "it cannot have sub-products itself.")
                    % rec.template_id.display_name)

    @api.onchange('sub_product_id')
    def _onchange_sub_product_id(self):
        if self.sub_product_id:
            if self.sub_product_id.seller_ids:
                if len(self.sub_product_id.seller_ids) > 1:
                    sorted_sellers = sorted(self.sub_product_id.seller_ids, key=lambda x: x.sequence)
                    self.vendor_id = sorted_sellers[0].name
                    self.qty = sorted_sellers[0].min_qty
                    self.standard_price_usd = sorted_sellers[0].price
                    self.standard_price_vnd = sorted_sellers[0].price_vnd
                else:
                    self.vendor_id = self.sub_product_id.seller_ids.name
                    self.qty = self.sub_product_id.seller_ids.min_qty
                    self.standard_price_usd = self.sub_product_id.seller_ids.price
                    self.standard_price_vnd = self.sub_product_id.seller_ids.price_vnd
