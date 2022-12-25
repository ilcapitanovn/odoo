# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

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


class ProductProduct(models.Model):
    _inherit = "product.product"


