from odoo import fields, models


class FreightCatalogAirline(models.Model):
    _name = "freight.catalog.airline"
    _description = "Freight Catalog Airline"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    description = fields.Char(translate=True)
    country_id = fields.Many2one('res.country', 'Country')
    icao = fields.Char(string="ICAO")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
