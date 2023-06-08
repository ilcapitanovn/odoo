# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.extensions import AsIs

from odoo import api, fields, models, tools
from odoo.tools import float_round


class SaleIncentiveAnalysisReport(models.Model):
    _name = "sale.incentive.analysis.report"
    _description = "Sale Incentive Analysis Report"
    _auto = False
    _rec_name = "user_id"

    def _get_default_currency(self):
        cur_id = self.env.context.get('wizard_currency_id')
        return cur_id

    @api.model
    def _get_selection_invoice_state(self):
        return self.env["account.move"].fields_get(allfields=["state"])["state"][
            "selection"
        ]

    user_id = fields.Many2one("res.users", "User", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    partner_id = fields.Many2one("res.partner", "Employee", readonly=True)
    incentive_id = fields.Many2one("sale.incentive", "Incentive", readonly=True)
    # incentive_section_id = fields.Many2one("sale.incentive.section", "Incentive Section", readonly=True)
    tax_income_id = fields.Many2one("account.tax.income", "Tax Income", readonly=True)
    # tax_income_section_id = fields.Many2one("account.tax.income.section", "Tax Income Section", readonly=True)

    # date_invoice = fields.Date("Date Invoice", readonly=True)
    #display_name = fields.Char("Name", readonly=True)
    incentive_name = fields.Char("Incentive Type", readonly=True)
    target_sales = fields.Float("Target Sales", readonly=True)

    sum_freehand = fields.Float("Freehand", readonly=True)
    sum_nominated = fields.Float("Nominated", readonly=True)
    sum_activities = fields.Float("Sales Activities", readonly=True)
    sum_all = fields.Float("Total", readonly=True)

    display_target_sales = fields.Float(compute="_compute_display_target_sales", string="Target Sales", readonly=True)
    display_sum_freehand = fields.Float(compute="_compute_incentive_and_tax", string="Freehand", readonly=True)
    display_sum_nominated = fields.Float(compute="_compute_incentive_and_tax", string="Nominated", readonly=True)
    display_sum_activities = fields.Float(compute="_compute_incentive_and_tax", string="Sales Activities", readonly=True)
    display_sum_all = fields.Float(compute="_compute_incentive_and_tax", string="Total", readonly=True)

    incentive = fields.Float(compute="_compute_incentive_and_tax", readonly=True)
    incentive_tax_amount = fields.Float(compute="_compute_incentive_and_tax", readonly=True)
    incentive_after_tax = fields.Float(compute="_compute_incentive_and_tax", readonly=True)

    # currency_id = fields.Many2one('res.currency', default=_get_default_currency, readonly=True)

    # invoice_line_id = fields.Many2one(
    #     "account.move.line", "Invoice line", readonly=True
    # )
    # commission_id = fields.Many2one("sale.commission", "Sale commission", readonly=True)

    # def _compute_currency(self):
    #     usd = self.env['res.currency'].search([('name', '=', 'USD')])
    #     return usd.id

    @api.depends('target_sales')
    def _compute_display_target_sales(self):
        cur = self.env.context.get('wizard_currency')
        rate = self.env.context.get('wizard_exchange_rate')

        for rec in self:
            if cur == 'VND':
                if rate > 0:
                    rec.display_target_sales = float_round(rec.target_sales * rate, precision_digits=0)
                else:
                    rec.display_target_sales = rec.target_sales
            else:
                rec.display_target_sales = rec.target_sales

    @api.depends('sum_freehand', 'sum_nominated', 'sum_activities', 'sum_all', 'target_sales')
    def _compute_incentive_and_tax(self):
        # cur = self.env.context.get('wizard_currency')
        # rate = self.env.context.get('wizard_exchange_rate')
        # if cur != 'VND' or rate <= 0:
        #     rate = 1
        rate = 1    # VND

        for rec in self:
            incentive = 0.0
            tax_amount = 0.0

            if rec.incentive_id and rec.incentive_id.section_ids:
                for sec in rec.incentive_id.section_ids:
                    amount_from = sec.percent_from * rec.display_target_sales / 100
                    amount_to = sec.percent_to * rec.display_target_sales / 100
                    if amount_from <= rec.sum_all and rec.sum_all < amount_to:
                        incentive = (sec.incentive_percent_month / 100) * \
                                    ((rec.sum_freehand * rec.incentive_id.target_freehand / 100) +
                                     (rec.sum_nominated * rec.incentive_id.target_nominated / 100) +
                                     (rec.sum_activities * rec.incentive_id.target_activities / 100))

                if incentive and rec.tax_income_id and rec.tax_income_id.section_ids:
                    incentive_tmp = incentive
                    if rec.tax_income_id.tax_income_type == 'section':
                        if len(rec.tax_income_id.section_ids) > 1:
                            sortedDescSections = sorted(rec.tax_income_id.section_ids, key=lambda x: x.amount_to, reverse=True)
                        else:
                            sortedDescSections = rec.tax_income_id.section_ids

                        for sec in sortedDescSections:
                            if sec.amount_from < incentive_tmp and incentive_tmp <= sec.amount_to:
                                incentive_to_tax = incentive_tmp - sec.amount_from
                                tax_amount += incentive_to_tax * sec.tax_rate_percent / 100
                                incentive_tmp -= incentive_to_tax
                    else:  # 'fixed'
                        tax_amount = incentive_tmp * rec.tax_income_id.fix_percent / 100

            """ Assign returned data """
            rec.display_sum_freehand = rec.sum_freehand * rate
            rec.display_sum_nominated = rec.sum_nominated * rate
            rec.display_sum_activities = rec.sum_activities * rate
            rec.display_sum_all = rec.sum_all * rate
            rec.incentive = incentive * rate
            rec.incentive_tax_amount = float_round(tax_amount * rate, precision_digits=0)
            rec.incentive_after_tax = rec.incentive - rec.incentive_tax_amount


                    # @api.depends("incentive")

    # @api.depends('po_commission_total')
    # def _compute_po_commission_in_vnd(self):
    #     usd = self.env['res.currency'].search([('name', '=', 'USD')])
    #     vnd = self.env['res.currency'].search([('name', '=', 'VND')])
    #     now = fields.Datetime.now()
    #
    #     for record in self:
    #         amount_vnd = usd._convert(record.po_commission_total, vnd, record.company_id, now)
    #         record.po_commission_total_vnd = amount_vnd

    def _select(self):
        select_str = """
            SELECT DISTINCT
                u.id AS id,
                u.id AS user_id,
                u.company_id AS company_id,
                u.partner_id AS partner_id,
                si.id AS incentive_id,
                ati.id AS tax_income_id,

                si.name AS incentive_name,
                p.target_sales AS target_sales,

                sum_freehand,
                sum_nominated,
                sum_activities,
                sum_freehand + sum_nominated + sum_activities AS sum_all
            FROM (
                SELECT user_id
                    , CASE WHEN order_type IS NULL THEN 'freehand' ELSE order_type END as order_type
                    , SUM(CASE WHEN order_type = 'freehand' THEN 
                            ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
                            - (so_amount_tax_vnd - po_amount_tax_vnd) 
                            - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.15)
                            ELSE 0 END) as sum_freehand
                    , SUM(CASE WHEN order_type = 'nominated' THEN 
                            ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
                            - (so_amount_tax_vnd - po_amount_tax_vnd) 
                            - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.15)
                            ELSE 0 END) as sum_nominated
                    , 0 as sum_activities
                FROM sale_profit_forwarder_analysis_report
                WHERE etd >= (SELECT date_from FROM sale_incentive_analysis_report_wizard ORDER BY id DESC FETCH FIRST 1 ROWS ONLY)
                    AND etd <= (SELECT date_to FROM sale_incentive_analysis_report_wizard ORDER BY id DESC FETCH FIRST 1 ROWS ONLY)
                GROUP BY user_id, order_type
            ) tblSum
            INNER JOIN res_users u ON tblSum.user_id = u.id
            INNER JOIN res_partner p ON u.partner_id = p.id
            LEFT JOIN sale_incentive si ON p.incentive_id = si.id
            LEFT JOIN sale_incentive_section sic ON sic.incentive_id = si.id
            LEFT JOIN account_tax_income ati ON si.tax_id = ati.id
            LEFT JOIN account_tax_income_section atis ON ati.id = atis.tax_id
        """

        # GROUP BY u.login, si.name, p.target_sales, sum_freehand, sum_nominated, sum_activities, sum_all

        return select_str

    # def _select(self):
    #     select_str = """
    #         SELECT DISTINCT
    #             u.id AS id
    #             , u.id AS user_id
    #             , u.company_id AS company_id
    #             , u.partner_id AS partner_id
    #             , si.id AS incentive_id
    #             , ati.id AS tax_income_id
    #
    #             , si.name AS incentive_name
    #             , p.target_sales AS target_sales
    #
    #             , CASE WHEN order_type = 'freehand' THEN margin ELSE 0 END as sum_freehand
    #             , CASE WHEN order_type = 'nominated' THEN margin ELSE 0 END as sum_nominated
    #             , 0 as sum_activities
    #         FROM sale_profit_forwarder_analysis_report tblView
    #         INNER JOIN res_users u ON tblView.user_id = u.id
    #         INNER JOIN res_partner p ON u.partner_id = p.id
    #         LEFT JOIN sale_incentive si ON p.incentive_id = si.id
    #         LEFT JOIN sale_incentive_section sic ON sic.incentive_id = si.id
    #         LEFT JOIN account_tax_income ati ON si.tax_id = ati.id
    #         LEFT JOIN account_tax_income_section atis ON ati.id = atis.tax_id
    #     """
    #
    #     # GROUP BY u.login, si.name, p.target_sales, sum_freehand, sum_nominated, sum_activities, sum_all
    #
    #     return select_str

    def _from(self):
        from_str = """
            freight_billing fbl
            INNER JOIN freight_booking fbk ON fbk.id = fbl.booking_id
            LEFT JOIN res_partner cus ON cus.id = fbl.partner_id
            LEFT JOIN freight_catalog_port pod ON fbk.port_discharge_id = pod.id
            LEFT JOIN freight_catalog_vessel fline ON fbk.vessel_id = fline.id
            LEFT JOIN res_users usale ON usale.id = fbl.user_id
            INNER JOIN res_partner psale ON usale.partner_id = psale.id
            LEFT JOIN sale_order so ON fbl.order_id = so.id
            LEFT JOIN purchase_order po on so.name = po.origin
        """
        return from_str

    # def _group_by(self):
    #     group_by_str = """
    #         GROUP BY ai.partner_id,
    #         ai.state,
    #         ai.date,
    #         ail.company_id,
    #         rp.id,
    #         pt.categ_id,
    #         ail.product_id,
    #         pt.uom_id,
    #         ail.id,
    #         aila.settled,
    #         aila.commission_id
    #     """
    #     return group_by_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s )",
            (
                AsIs(self._table),
                AsIs(self._select()),
                # AsIs(self._from()),
                # AsIs(self._group_by()),
            ),
        )
