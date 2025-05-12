# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


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
    is_no_vat = fields.Boolean(string="No Customer Taxes", default=False)

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

    @api.onchange('is_no_vat')
    def _onchange_is_no_vat(self):
        if self.is_no_vat:
            self.taxes_id = [(6, 0, [])]    # Mark empty if no vat

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

    @api.model
    def action_automate_configure_mto_product(self):
        try:
            mto_route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)
            buy_route = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)

            if not mto_route or not buy_route:
                raise UserError("Buy route or MTO route not found. Ensure the stock module is installed.")

            # Get the supplier (res.partner)
            default_supplier = self.env['res.partner'].search([('name', '=', 'VIETTOAN')], limit=1)
            if not default_supplier.exists():
                raise UserError("Default supplier [VIETTOAN] not found.")

            domain = [
                ('detailed_type', '=', 'consu')
            ]
            products = self.env['product.template'].sudo().search(domain)
            products_empty_routes = products.filtered(lambda p: not p.route_ids)
            products_missing_routes = products.filtered(
                lambda p: p.route_ids and (mto_route.id not in p.route_ids.ids or buy_route.id not in p.route_ids.ids)
            )

            count_empty_processed = 0
            for pro in products_empty_routes:
                if not pro.route_ids:
                    # Assign Buy and MTO route
                    obj = {'route_ids': [(4, buy_route.id), (4, mto_route.id)]}

                    # Make sure at least one seller is assigned
                    if not pro.seller_ids:
                        supplier_info = {
                            'name': default_supplier.id,
                            'company_id': self.env.company.id,
                            'product_tmpl_id': pro.id,
                            'price': pro.standard_price,
                            'min_qty': 0
                        }
                        obj['seller_ids'] = [(0, 0, supplier_info)]

                    pro.write(obj)
                    print(f"Empty Buy and MTO route assigned to product: {pro.name}")
                    count_empty_processed += 1

            count_missing_processed = 0
            for pro in products_missing_routes:
                obj = {}
                if mto_route.id not in pro.route_ids.ids and buy_route.id not in pro.route_ids.ids:
                    obj['route_ids'] = [(4, buy_route.id), (4, mto_route.id)]
                    print(f"Both missing Buy and MTO route assigned to product: {pro.name}")
                    count_empty_processed += 1
                elif mto_route.id not in pro.route_ids.ids:
                    obj['route_ids'] = [(4, mto_route.id)]
                    print(f"Missing MTO route assigned to product: {pro.name}")
                    count_missing_processed += 1
                elif buy_route.id not in pro.route_ids.ids:
                    obj['route_ids'] = [(4, buy_route.id)]
                    print(f"Missing Buy route assigned to product: {pro.name}")
                    count_missing_processed += 1

                # Make sure at least one seller is assigned
                if not pro.seller_ids:
                    supplier_info = {
                        'name': default_supplier.id,
                        'company_id': self.env.company.id,
                        'product_tmpl_id': pro.id,
                        'price': pro.standard_price,
                        'min_qty': 0
                    }
                    obj['seller_ids'] = [(0, 0, supplier_info)]

                if obj:
                    pro.write(obj)

            print(f"action_automate_configure_mto_product - executed successful. "
                  f"Empty products processed: {count_empty_processed}. "
                  f"Missing products processed: {count_missing_processed}")

        except Exception as e:
            _logger.exception("action_automate_configure_mto_product - Exception: " + str(e))


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
