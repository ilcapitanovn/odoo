# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_default_exchange_rate(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        vnd_rate = vnd.rate if vnd else 0
        return float_round(vnd_rate, precision_digits=0)

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    def _get_default_list_price_vnd(self):
        vnd_price = 0.0
        if self.list_price and self.exchange_rate:
            vnd_price = self.list_price * self.exchange_rate
        return float_round(vnd_price, precision_digits=0)

    def _get_default_standard_price_vnd(self):
        vnd_standard_price = 0.0
        if self.standard_price and self.exchange_rate:
            vnd_standard_price = self.standard_price * self.exchange_rate
        return float_round(vnd_standard_price, precision_digits=0)

    port_loading_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Loading Port"
    )
    port_discharge_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Discharge Port"
    )
    container_id = fields.Many2one(
        comodel_name="freight.catalog.container", string="Container Type"
    )
    vessel_id = fields.Many2one(
        comodel_name="freight.catalog.vessel", string="Shipping Line"
    )

    exchange_rate = fields.Float(string='VND/USD rate', default=_get_default_exchange_rate, readonly=True,
                                 help='The rate of VND per USD.', tracking=True, store=True)

    product_currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id,
                                          tracking=True, required=True)
    vnd_currency_id = fields.Many2one('res.currency', 'Vietnamese Currency', compute="_compute_vnd_currency_id")
    list_price_vnd = fields.Float(
        'Sales Price (VND)', default=_get_default_list_price_vnd, tracking=True,
        digits='Product Price', help="Price at which the product is sold to customers in VND.",
    )
    standard_price_vnd = fields.Float(
        'Cost (VND)', default=_get_default_standard_price_vnd, tracking=True,
        digits='Product Price', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the next unit that will leave the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")
    flag_just_updated = fields.Boolean(compute="_compute_flag_just_updated")

    def _compute_flag_just_updated(self):
        self.flag_just_updated = False

    def _compute_vnd_currency_id(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        for rec in self:
            rec.vnd_currency_id = vnd.id or False

    @api.onchange('seller_ids')
    def _onchange_supplier_price(self):
        if not self.seller_ids:
            return

        if len(self.seller_ids) > 1:
            # variant_prices = self.mapped('seller_ids.price')
            # new_price = min(variant_prices)
            ''' Get the first supplier '''
            sorted_sellers = sorted(self.seller_ids, key=lambda x: x.sequence)
            new_price = sorted_sellers[0].price
        else:
            new_price = self.seller_ids.price

        if new_price > 0:
            self.standard_price = new_price

    @api.onchange('list_price')
    def _onchange_list_price(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.list_price_vnd = self.list_price * self.exchange_rate
            self.flag_just_updated = True

    @api.onchange('list_price_vnd')
    def _onchange_list_price_vnd(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.list_price = self.list_price_vnd / self.exchange_rate
            self.flag_just_updated = True

    @api.onchange('standard_price')
    def _onchange_standard_price(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.standard_price_vnd = self.standard_price * self.exchange_rate
            self.flag_just_updated = True

    @api.onchange('standard_price_vnd')
    def _onchange_standard_price_vnd(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.standard_price = self.standard_price_vnd / self.exchange_rate
            self.flag_just_updated = True

    def update_exchange_rate(self):
        self.ensure_one()
        self.exchange_rate = self._get_default_exchange_rate()


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    exchange_rate = fields.Float(related="product_tmpl_id.exchange_rate", string="VND/USD rate")
    price_vnd = fields.Float(
        'Price (VND)', compute='_compute_price_vnd', readonly=False, store=True, tracking=True,
        help="The price to purchase a product in VND")
    flag_just_updated = fields.Boolean(compute="_compute_flag_just_updated")

    def _compute_flag_just_updated(self):
        self.flag_just_updated = False

    @api.depends('price')
    def _compute_price_vnd(self):
        for rec in self:
            if rec.exchange_rate and not rec.flag_just_updated:
                rec.price_vnd = rec.price * rec.exchange_rate
                rec.flag_just_updated = True

    @api.onchange('price_vnd')
    def _onchange_price_vnd(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.price = self.price_vnd / self.exchange_rate
            self.flag_just_updated = True


class ProductProduct(models.Model):
    _inherit = "product.product"


