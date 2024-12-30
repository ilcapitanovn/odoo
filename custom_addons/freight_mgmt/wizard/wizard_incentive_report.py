# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleIncentiveAnalysisReportWiward(models.TransientModel):
    _name = "sale.incentive.analysis.report.wizard"
    _description = "Wizard for calculating sales incentive report"

    def _get_default_currency(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')])
        return vnd.id

    date_from = fields.Date("Report from", required=True, default=fields.Date.today())
    date_to = fields.Date("Report to", required=True, default=fields.Date.today())
    currency_ids = fields.Many2one('res.currency', default=_get_default_currency)
    currency_name = fields.Char(related="currency_ids.name")
    exchange_rate = fields.Float("Exchange Rate", default=22000)

    # @api.onchange('currency_ids')
    # def _onchange_methods(self):

    def action_view_report(self):
        self.ensure_one()

        context = {
            'search_default_group_by_incentive': 1,
            'wizard_currency': self.currency_ids.name,
            'wizard_currency_id': self.currency_ids.id,
            'wizard_exchange_rate': self.exchange_rate,
            'wizard_date_from': self.date_from,
            'wizard_date_to': self.date_to
        }

        # go to results
        res = {
            "name": _("Sales Incentive Report"),
            "type": "ir.actions.act_window",
            "res_model": "sale.incentive.analysis.report",
            'view_mode': 'tree',
            # "views": [[False, "list"], [False, "form"]],
            'views': [(self.env.ref('freight_mgmt.view_sale_incentive_analysis_view_list').id, 'tree')],
            'context': context,
            'target': 'main',
            'search_view_id': [self.env.ref('freight_mgmt.view_sale_incentive_analysis_search').id],
            'view_id': [self.env.ref('freight_mgmt.view_sale_incentive_analysis_view_list').id]
        }

        is_manager = self.user_has_groups("sales_team.group_sale_manager")
        if not is_manager:
            res['domain'] = [('user_id', '=', self.env.uid)]

        return res

