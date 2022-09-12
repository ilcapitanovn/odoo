from odoo import fields, models


class FreightCatalogContainer(models.Model):
    _name = "freight.catalog.container"
    _description = "Freight Catalog Container"

    name = fields.Char()
    code = fields.Char(required=True)
    description = fields.Char(translate=True)
    size = fields.Integer(string="Size (ft)")
    volume = fields.Integer(string="Volume (cbm)")
    weight = fields.Integer(string="Weight (kg)")
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
