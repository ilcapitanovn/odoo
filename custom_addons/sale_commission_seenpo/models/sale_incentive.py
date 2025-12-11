# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class SaleIncentive(models.Model):
    _name = "sale.incentive"
    _description = "Incentive in sales"

    name = fields.Char("Name", required=True)
    section_ids = fields.One2many(      # 6th Update
        string="Active Sections",
        comodel_name="sale.incentive.section",
        inverse_name="incentive_id",
        domain=[('revision_no', '=', 6)]
    )
    section_ids_5th_update = fields.One2many(
        "sale.incentive.section",
        "incentive_id",
        string="Old Sections  5th Update",
        domain=[('revision_no', '=', 5)]
    )
    section_ids_3rd_update = fields.One2many(
        "sale.incentive.section",
        "incentive_id",
        string="Old Sections - 3rd Update",
        domain=[('revision_no', '=', 3)]
    )

    target_freehand = fields.Float(string="Freehand rate (%)", default=85)
    target_nominated = fields.Float(string="Nominated rate (%)", default=10)
    target_activities = fields.Float(string="Sales activity rate (%)", default=5)

    apply_sales_team = fields.Boolean()
    active = fields.Boolean(default=True)
    amount_base_type = fields.Selection(
        selection=[("gross_amount", "Gross Amount"), ("net_amount", "Net Amount")],
        string="Base",
        required=True,
        default="net_amount",
    )
    invoice_state = fields.Selection(
        [("open", "Invoice Based"), ("paid", "Payment Based")],
        string="Invoice Status",
        required=True,
        default="paid",
    )

    tax_id = fields.Many2one('account.tax.income', 'Income Tax')

    def calculate_section(self, base):
        self.ensure_one()
        for section in self.section_ids:
            if section.amount_from <= base <= section.amount_to:
                return base * section.percent / 100.0
        return 0.0

    @api.constrains("target_freehand", "target_nominated", "target_activities")
    def _check_activities_weights(self):
        for rec in self:
            if rec.target_freehand > 100.0 or rec.target_nominated > 100.0 or rec.target_activities > 100.0:
                raise exceptions.ValidationError(
                    _("The activity rates cannot be greater than 100%.")
                )

    @api.depends("section_ids")
    def _compute_section_ids_5th_update(self):
        for rec in self:
            rec.section_ids_5th_update = rec.section_ids.filtered(
                lambda r: r.revision_no == 5
            )

    @api.depends("section_ids")
    def _compute_section_ids_3rd_update(self):
        for rec in self:
            rec.section_ids_3rd_update = rec.section_ids.filtered(
                lambda r: r.revision_no == 3
            )


class SaleIncentiveSection(models.Model):
    _name = "sale.incentive.section"
    _description = "Incentive section"

    incentive_id = fields.Many2one("sale.incentive", string="Active Incentive")

    percent_from = fields.Float(string="From (%)")
    percent_to = fields.Float(string="To (%)")
    incentive_percent_month = fields.Float(string="Incentive By Month (%)", required=True)
    incentive_percent_year = fields.Float(string="Incentive By Year (%)")
    date_start = fields.Date(string='Date Start', copy=False)
    date_end = fields.Date(string='Date End', copy=False)
    revision_no = fields.Integer(string="Revision No.", default=6,
                                 help="Revision number of the incentive rule. Increase when rule is updated.")

    @api.constrains("percent_from", "percent_to")
    def _check_percents(self):
        for section in self:
            if section.percent_to < section.percent_from:
                raise exceptions.ValidationError(
                    _("The lower limit cannot be greater than upper one.")
                )
