from odoo import fields, models


class FreightCatalogPort(models.Model):
    _name = "freight.catalog.port"
    _description = "Freight Catalog Port"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, translate=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    printing_name = fields.Char(string="Printing Name", translate=True, help="The name is printed in BL", tracking=True)
    description = fields.Char(translate=True, tracking=True)
    country_id = fields.Many2one('res.country', 'Country', tracking=True)
    state_ids = fields.Many2many('res.country.state', string='Federal States', tracking=True)
    port_type = fields.Selection(
        selection=[("ocean", "Ocean"), ("land", "Land"), ("air", "Air")],
        string="Port Type", help='Type of Port', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
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
