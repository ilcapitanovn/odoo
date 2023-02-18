# Copyright 2022 BaoThinhSoftware Apps (https://baothinh.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DashboardConfigurationUpdateWizard(models.TransientModel):
    _name = "dashboard.configuration.update.wizard"
    _description = "Dashboard Configuration Update Wizard"

    def _default_date_range(self):
        date_range = self.env['ir.config_parameter'].sudo().get_param('odoo_dynamic_dashboard.date_range')
        return date_range

    def _default_compared_to(self):
        compared_to = self.env['ir.config_parameter'].sudo().get_param('odoo_dynamic_dashboard.compared_to')
        return compared_to

    x_date_range = fields.Selection(
        selection=[("today", "Today"), ("yesterday", "Yesterday"), ("this_week", "This week"),
                   ("last_week", "Last week"), ("next_week", "Next week"), ("this_month", "This month"),
                   ("last_month", "Last month"),
                   ("next_month", "Next month"), ("this_quarter", "This quarter"), ("last_quarter", "Last quarter"),
                   ("next_quarter", "Next quarter"), ("this_year", "This year"), ("last_year", "Last year"),
                   ("next_year", "Next year")],
        string="Date range", default=_default_date_range,
        help='Period time filter for report')
    x_compared_to = fields.Selection(
        selection=[("previous_week", "Previous week"), ("previous_month", "Previous month"),
                   ("year_before", "Year before")],
        string="Compared To", default=_default_compared_to,
        help='See how it compared to previous')

    def action_update(self):
        self.ensure_one()

        self.env['ir.config_parameter'].sudo().set_param('odoo_dynamic_dashboard.date_range', self.x_date_range)
        self.env['ir.config_parameter'].sudo().set_param('odoo_dynamic_dashboard.compared_to', self.x_compared_to)

        blocks = self.env['dashboard.block'].search([])
        for block in blocks:
            block.x_date_range = self.x_date_range
            block.x_compared_to = self.x_compared_to

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
