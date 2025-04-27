# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.extensions import AsIs

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import float_round


class SaleIncentiveAnalysisReport(models.Model):
    _name = "sale.incentive.analysis.report"
    _description = "Sale Incentive Analysis Report"
    _auto = False
    _rec_name = "user_id"

    user_id = fields.Many2one("res.users", "User", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    partner_id = fields.Many2one("res.partner", "Employee", readonly=True)
    incentive_id = fields.Many2one("sale.incentive", "Incentive", readonly=True)
    # incentive_section_id = fields.Many2one("sale.incentive.section", "Incentive Section", readonly=True)
    tax_income_id = fields.Many2one("account.tax.income", "Tax Income", readonly=True)
    # tax_income_section_id = fields.Many2one("account.tax.income.section", "Tax Income Section", readonly=True)

    bill_no = fields.Char("BILL NO", readonly=True)
    pod_id = fields.Many2one("freight.catalog.port", "POL/D", readonly=True)
    date_order = fields.Date("Order Date", readonly=True)
    etd = fields.Date("ETD", readonly=True)
    invoice_date = fields.Date("Invoice Date", readonly=True)
    payment_state = fields.Char("Payment Status", readonly=True)

    incentive_name = fields.Char("Incentive Type", readonly=True)
    target_sales = fields.Float("Target Sales", readonly=True)

    sum_freehand = fields.Float("Freehand", readonly=True)
    sum_nominated = fields.Float("Nominated", readonly=True)
    sum_activities = fields.Float("Sales Activities", readonly=True)
    sum_all = fields.Float("Total", readonly=True)

    display_pod = fields.Char(compute="_compute_display_pod", readonly=True)
    display_target_sales = fields.Float(compute="_compute_display_target_sales", string="Target Sales", readonly=True)

    incentive = fields.Float(compute="_compute_incentive_and_tax", readonly=True)
    incentive_tax_amount = fields.Float(compute="_compute_incentive_and_tax", readonly=True)
    incentive_after_tax = fields.Float(compute="_compute_incentive_and_tax", readonly=True)

    display_achieve = fields.Integer(compute="_compute_display_achieve", string="Achieve", readonly=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        '''
        Calculate to display total if using group by
        '''
        exchange_rate = int(self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.default_usd_vnd_exchange_rate', -1))
        res = super(SaleIncentiveAnalysisReport, self).read_group(domain, fields, groupby, offset=offset,
                                                                  limit=limit, orderby=orderby, lazy=lazy)

        fields_to_calculate_total = [
            'display_target_sales',
            'sum_freehand',
            'sum_nominated',
            'sum_all',
            'incentive',
            'incentive_tax_amount',
            'incentive_after_tax',
            'display_achieve'
        ]
        for field in fields_to_calculate_total:
            if field in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        total = 0.0
                        for record in lines:
                            if field == 'display_target_sales':
                                total = record['target_sales'] * exchange_rate  # Only need first record, no sum
                                break
                            elif field == 'display_achieve':
                                break
                            else:
                                total += record[field]
                        line[field] = total

                        if field == 'display_achieve':
                            sum_all = line['sum_all']
                            target = line['display_target_sales']
                            val = 1 if sum_all > target * 0.5 else 0
                            line[field] = val

        return res

    @api.depends('pod_id')
    def _compute_display_pod(self):
        for record in self:
            display_pod = record.pod_id.name if record.pod_id else ''
            record.display_pod = (" ".join(display_pod.split()[:3])).capitalize()    # get first two words

    @api.depends('target_sales', 'sum_all')
    def _compute_display_achieve(self):
        for record in self:
            record.display_achieve = 0  # Khong dat

    @api.depends('target_sales')
    def _compute_display_target_sales(self):
        for rec in self:
            rec.display_target_sales = 0

    @api.depends('sum_freehand', 'sum_nominated', 'sum_activities', 'sum_all', 'target_sales')
    def _compute_incentive_and_tax(self):
        exchange_rate = int(self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.default_usd_vnd_exchange_rate', -1))

        for rec in self:
            res = self.calculate_incentive_and_tax(rec, exchange_rate)
            rec.incentive = res['incentive']
            rec.incentive_tax_amount = res['incentive_tax_amount']
            rec.incentive_after_tax = res['incentive_after_tax']

    @staticmethod
    def calculate_incentive_and_tax(rec, exchange_rate_vnd):
        incentive = 0.0
        tax_amount = 0.0

        target_sales_vnd = rec.target_sales * exchange_rate_vnd

        if rec.incentive_id and rec.incentive_id.section_ids:
            for sec in rec.incentive_id.section_ids:
                amount_from = sec.percent_from * target_sales_vnd / 100
                amount_to = sec.percent_to * target_sales_vnd / 100
                if amount_from <= rec.sum_all < amount_to:
                    incentive = (sec.incentive_percent_month / 100) * \
                                ((rec.sum_freehand * rec.incentive_id.target_freehand / 100) +
                                 (rec.sum_nominated * rec.incentive_id.target_nominated / 100) +
                                 (rec.sum_activities * rec.incentive_id.target_activities / 100))

            if incentive and rec.tax_income_id and rec.tax_income_id.section_ids:
                incentive_tmp = incentive
                if rec.tax_income_id.tax_income_type == 'section':
                    if len(rec.tax_income_id.section_ids) > 1:
                        sortedDescSections = sorted(rec.tax_income_id.section_ids, key=lambda x: x.amount_to,
                                                    reverse=True)
                    else:
                        sortedDescSections = rec.tax_income_id.section_ids

                    for sec in sortedDescSections:
                        if sec.amount_from < incentive_tmp <= sec.amount_to:
                            incentive_to_tax = incentive_tmp - sec.amount_from
                            tax_amount += incentive_to_tax * sec.tax_rate_percent / 100
                            incentive_tmp -= incentive_to_tax
                else:  # 'fixed'
                    tax_amount = incentive_tmp * rec.tax_income_id.fix_percent / 100

        result = {
            'incentive': incentive,
            'incentive_tax_amount': float_round(tax_amount, precision_digits=0),
            'incentive_after_tax': rec.incentive - rec.incentive_tax_amount
        }

        return result

    def action_print_sale_incentive_report(self):
        return self.env.ref('freight_mgmt.freight_sale_incentive_report_template_action').report_action(self)

    def action_view_sale_incentive_details(self):
        active_ids = self.env.context.get('active_ids', [])
        if len(active_ids) == 1:
            title_name = self.display_name
            context = {
                'search_default_group_by_customer': 1,
            }

            domain = [('id', '=', self.id)]

            profit_tree = self.env.ref('freight_mgmt.view_sale_profit_forwarder_analysis_view_list', False)
            view_id_tree = self.env['ir.ui.view'].sudo().search(
                [('name', '=', "sale.profit.forwarder.analysis.view.list")])
            return {
                'name': title_name,
                'type': 'ir.actions.act_window',
                'res_model': 'sale.profit.forwarder.analysis.report',
                'binding_view_types': 'list',
                'view_mode': 'tree',
                'views': [(view_id_tree[0].id, 'tree')],
                'view_id': profit_tree.id,
                'target': 'main',
                'context': context,
                'domain': domain,
            }
        elif len(active_ids) > 1:
            raise UserError("You can only select one record to view details.")
        else:
            raise UserError("Please select a record to view its details.")


    def _select(self):
        ''' This has been deprecated due to new policy of incentive is applied from 01 June 2023 '''

        # select_str = """
        #     SELECT DISTINCT
        #         u.id AS id,
        #         u.id AS user_id,
        #         u.company_id AS company_id,
        #         u.partner_id AS partner_id,
        #         si.id AS incentive_id,
        #         ati.id AS tax_income_id,
        #
        #         si.name AS incentive_name,
        #         p.target_sales AS target_sales,
        #
        #         sum_freehand,
        #         sum_nominated,
        #         sum_activities,
        #         sum_freehand + sum_nominated + sum_activities AS sum_all
        #     FROM (
        #         SELECT user_id
        #             , SUM(CASE WHEN order_type = 'freehand' THEN
        #                     ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
        #                     - (so_amount_tax_vnd - po_amount_tax_vnd)
        #                     - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.15)
        #                     ELSE 0 END) as sum_freehand
        #             , SUM(CASE WHEN order_type = 'nominated' THEN
        #                     ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
        #                     - (so_amount_tax_vnd - po_amount_tax_vnd)
        #                     - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.15)
        #                     ELSE 0 END) as sum_nominated
        #             , 0 as sum_activities
        #         FROM sale_profit_forwarder_analysis_report
        #         WHERE etd >= (SELECT date_from FROM sale_incentive_analysis_report_wizard ORDER BY id DESC FETCH FIRST 1 ROWS ONLY)
        #             AND etd <= (SELECT date_to FROM sale_incentive_analysis_report_wizard ORDER BY id DESC FETCH FIRST 1 ROWS ONLY)
        #         GROUP BY user_id
        #     ) tblSum
        #     INNER JOIN res_users u ON tblSum.user_id = u.id
        #     INNER JOIN res_partner p ON u.partner_id = p.id
        #     LEFT JOIN sale_incentive si ON p.incentive_id = si.id
        #     LEFT JOIN sale_incentive_section sic ON sic.incentive_id = si.id
        #     LEFT JOIN account_tax_income ati ON si.tax_id = ati.id
        #     LEFT JOIN account_tax_income_section atis ON ati.id = atis.tax_id
        # """

        ''' New incentive policy is available since 01 June 2023 '''
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

                        CASE WHEN si.target_freehand > 0 THEN sum_freehand ELSE 0 END sum_freehand,
                        CASE WHEN si.target_nominated > 0 THEN sum_nominated ELSE 0 END sum_nominated,
                        CASE WHEN si.target_activities > 0 THEN sum_activities ELSE 0 END sum_activities,
                        (CASE WHEN si.target_freehand > 0 THEN sum_freehand ELSE 0 END + CASE WHEN si.target_nominated > 0 THEN sum_nominated ELSE 0 END + CASE WHEN si.target_activities > 0 THEN sum_activities ELSE 0 END) AS sum_all
                    FROM (
                        SELECT user_id
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
                        WHERE payment_state in ('in_payment', 'paid')
                            AND invoice_date >= (SELECT date_from FROM sale_incentive_analysis_report_wizard ORDER BY id DESC FETCH FIRST 1 ROWS ONLY)
                            AND invoice_date <= (SELECT date_to FROM sale_incentive_analysis_report_wizard ORDER BY id DESC FETCH FIRST 1 ROWS ONLY)
                        GROUP BY user_id
                    ) tblSum
                    INNER JOIN res_users u ON tblSum.user_id = u.id
                    INNER JOIN res_partner p ON u.partner_id = p.id
                    LEFT JOIN sale_incentive si ON p.incentive_id = si.id
                    LEFT JOIN sale_incentive_section sic ON sic.incentive_id = si.id
                    LEFT JOIN account_tax_income ati ON si.tax_id = ati.id
                    LEFT JOIN account_tax_income_section atis ON ati.id = atis.tax_id
                    WHERE si.target_freehand * sum_freehand + si.target_nominated * sum_nominated + si.target_activities * sum_activities > 0
                """

        # GROUP BY u.login, si.name, p.target_sales, sum_freehand, sum_nominated, sum_activities, sum_all

        return select_str

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

    @staticmethod
    def _select_v2():
        '''
        New incentive policy is available since 01 June 2023.
         Updates to make it more similar excel file from accounting
        '''
        select_str = """
            SELECT DISTINCT
                tblSum.id AS id,
                u.id AS user_id,
                u.company_id AS company_id,
                u.partner_id AS partner_id,
                si.id AS incentive_id,
                ati.id AS tax_income_id,
                
                si.name AS incentive_name,
                p.target_sales AS target_sales,

                tblSum.bill_no AS bill_no,
                tblSum.pod_id AS pod_id,
                tblSum.date_order AS date_order,
                tblSum.etd AS etd,
                tblSum.invoice_date AS invoice_date,
                tblSum.payment_state AS payment_state,

                sum_freehand,
                sum_nominated,
                sum_activities,
                sum_freehand + sum_nominated + sum_activities AS sum_all
        """

        return select_str

    @staticmethod
    def _subquery_profit_forwarder_report():
        subquery_str = """
            SELECT id
                , user_id
                , bill_no
                , pod_id
                , date_order
                , etd
                , invoice_date
                , payment_state
                , CASE WHEN order_type = 'freehand' THEN 
                        ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
                        - (so_amount_tax_vnd - po_amount_tax_vnd) 
                        - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.15)
                        ELSE 0 END as sum_freehand
                , CASE WHEN order_type = 'nominated' THEN 
                        ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
                        - (so_amount_tax_vnd - po_amount_tax_vnd) 
                        - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.15)
                        ELSE 0 END as sum_nominated
                , 0 as sum_activities
            FROM sale_profit_forwarder_analysis_report
        """

        return subquery_str

    def _from_v2(self):
        from_str = f"""
            ({self._subquery_profit_forwarder_report()}) tblSum
            INNER JOIN res_users u ON tblSum.user_id = u.id
            INNER JOIN res_partner p ON u.partner_id = p.id
            LEFT JOIN sale_incentive si ON p.incentive_id = si.id
            LEFT JOIN sale_incentive_section sic ON sic.incentive_id = si.id
            LEFT JOIN account_tax_income ati ON si.tax_id = ati.id
            LEFT JOIN account_tax_income_section atis ON ati.id = atis.tax_id
        """
        return from_str

    def _where_v2(self):
        where_str = """
            WHERE si.target_freehand * sum_freehand + si.target_nominated * sum_nominated + si.target_activities * sum_activities > 0
        """
        return where_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s FROM ( %s ) )",
            (
                AsIs(self._table),
                AsIs(self._select_v2()),
                AsIs(self._from_v2()),
                # AsIs(self._where_v2()),
                # AsIs(self._group_by()),
            ),
        )


class ReportSaleIncentiveAnalysis(models.AbstractModel):
    _name = 'report.freight_mgmt.report_print_sale_incentive_template'
    _description = 'Sale Incentive Report With Grouping'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["sale.incentive.analysis.report"].browse(docids)
        exchange_rate = int(self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.default_usd_vnd_exchange_rate', -1))

        ''' Method 1: Manual Nested Grouping (More Control) '''
        grouped_incentives = {}
        for doc in docs:
            grouping_incentive_name = doc.incentive_name
            grouping_sale_name = doc.display_name

            if grouping_incentive_name not in grouped_incentives:
                grouped_incentives[grouping_incentive_name] = {}

            if grouping_sale_name not in grouped_incentives[grouping_incentive_name]:
                grouped_incentives[grouping_incentive_name][grouping_sale_name] = []

            grouped_incentives[grouping_incentive_name][grouping_sale_name].append(doc)

        processed_groups = []
        months = []
        years = []
        for grouping_incentive_type, sale_groups in grouped_incentives.items():
            incentive_data = []
            total_incentive_type = 0.0
            for grouping_salesman, incentives in sale_groups.items():
                # salesman_sum_freehand_total = sum(incentive.sum_freehand for incentive in incentives)
                salesman_sum_freehand_total = 0.0
                salesman_sum_nominated_total = 0.0
                salesman_incentive_after_tax_total = 0.0
                display_target_sales = 0.0
                for incentive in incentives:
                    salesman_sum_freehand_total += incentive.sum_freehand
                    salesman_sum_nominated_total += incentive.sum_nominated
                    res = SaleIncentiveAnalysisReport.calculate_incentive_and_tax(incentive, exchange_rate)
                    salesman_incentive_after_tax_total += res['incentive_after_tax']
                    if display_target_sales == 0.0:
                        display_target_sales = incentive.target_sales * exchange_rate
                    if incentive.etd:
                        month = incentive.etd.strftime('%m')
                        year = incentive.etd.strftime('%Y')
                        if month not in months:
                            months.append(month)
                        if year not in years:
                            years.append(year)

                salesman_sum_revenue_total = salesman_sum_freehand_total + salesman_sum_nominated_total
                achieve = salesman_sum_revenue_total > display_target_sales * 0.5

                incentive_data.append({
                    'sale_name': grouping_salesman,
                    'display_target_sales': display_target_sales,
                    'sum_freehand_total': salesman_sum_freehand_total,
                    'sum_nominated_total': salesman_sum_nominated_total,
                    'sum_revenue_total': salesman_sum_revenue_total,
                    'incentive_after_tax_total': salesman_incentive_after_tax_total,
                    'achieve': achieve,
                    'incentives': incentives
                })
                total_incentive_type += salesman_incentive_after_tax_total

            processed_groups.append({
                'incentive_type': grouping_incentive_type,
                'incentive_data': incentive_data,
                'total_incentive_type': total_incentive_type
            })

        ''' Method 2: Using read_group with Multiple groupby Fields: '''
        # grouped_records = self.env['sale.incentive.analysis.report'].read_group(
        #     domain=[('id', 'in', docs.ids)],
        #     fields=['sum_freehand:sum', 'sum_nominated:sum', 'sum_all:sum'],
        #     groupby=['incentive_name', 'partner_id']
        # )

        if len(months) > 1:
            months.sort()
        if len(years) > 1:
            years.sort()
        report_time = ",".join(months) + "/" + ",".join(years)

        return {
            'doc_ids': docs.ids,
            'docs': docs,
            'incentive_month': report_time,
            'grouped_records': processed_groups
        }
