from odoo import fields, models


class FreightCatalogIncoterm(models.Model):
    _name = "freight.catalog.incoterm"
    _description = "Freight Catalog Incoterm"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    description = fields.Char(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
