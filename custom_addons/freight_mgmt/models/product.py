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


class ProductProduct(models.Model):
    _inherit = "product.product"


