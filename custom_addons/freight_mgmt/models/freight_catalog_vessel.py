from odoo import fields, models


class FreightCatalogVessel(models.Model):
    _name = "freight.catalog.vessel"
    _description = "Freight Catalog Vessel"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    description = fields.Char(translate=True)
    country_id = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
