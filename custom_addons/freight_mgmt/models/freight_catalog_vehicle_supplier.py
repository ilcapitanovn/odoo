from odoo import fields, models


class FreightCatalogVehicleSupplier(models.Model):
    _name = "freight.catalog.vehicle.supplier"
    _description = "Freight Catalog Vehicle Supplier"

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    phone = fields.Char()
    email = fields.Char()
    address = fields.Char()
    description = fields.Char(translate=True)
    country_id = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.code + " - " + rec.name))
        return result
