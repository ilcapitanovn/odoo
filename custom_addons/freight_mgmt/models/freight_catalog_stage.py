from odoo import fields, models


class FreightCatalogStage(models.Model):
    _name = "freight.catalog.stage"
    _description = "Freight Catalog Stage"
    _order = "sequence, id"

    name = fields.Char(string="Stage Name", required=True, translate=True)
    description = fields.Html(translate=True, sanitize_style=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    confirmed = fields.Boolean()
    completed = fields.Boolean()
    mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template",
        domain=[("model", "=", "freight.catalog")],
        help="If set an email will be sent to the "
        "appropriate members when the booking reaches this step.",
    )
    fold = fields.Boolean(
        string="Folded in Kanban",
        help="This stage is folded in the kanban view "
        "when there are no records in that stage "
        "to display.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
