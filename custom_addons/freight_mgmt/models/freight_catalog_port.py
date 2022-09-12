from odoo import fields, models


class FreightCatalogPort(models.Model):
    _name = "freight.catalog.port"
    _description = "Freight Catalog Port"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    description = fields.Char(translate=True)
    country_id = fields.Many2one('res.country', 'Country')
    state_ids = fields.Many2many('res.country.state', string='Federal States')
    port_type = fields.Selection(
        selection=[("air", "Air"), ("ocean", "Ocean")],
        string="Port Type", help='Type of Port')
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
