# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import pytz
import itertools
from datetime import datetime
from psycopg2.extensions import AsIs

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import float_round


class SaleIncentiveAnalysisReport(models.Model):
    _name = "sale.incentive.analysis.report"
    _description = "Sale Incentive Analysis Report"
    _auto = False
    _rec_name = "user_id"
    _order = "incentive_name DESC"

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
    etd_formatted = fields.Char(compute="_compute_format_etd", string="ETD", readonly=True, store=False)
    invoice_date = fields.Date("Invoice Date", readonly=True)
    payment_state = fields.Char("Payment Status", readonly=True)

    incentive_name = fields.Char("Incentive Type", readonly=True)
    target_sales = fields.Float("Target Sales", readonly=True)

    po_amount_untaxed = fields.Float("Chua VAT (I)", readonly=True)
    so_amount_untaxed = fields.Float("Chua VAT (O)", readonly=True)
    margin = fields.Float("Margin", readonly=True)

    order_type = fields.Char("Freehand or Nominated", readonly=True)
    po_amount_untaxed_vnd = fields.Float("COST Input (No_VAT)", readonly=True)
    po_amount_total_vnd = fields.Float("COST Input (With_VAT)", readonly=True)
    po_amount_tax_vnd = fields.Float("COST Input (VAT)", readonly=True)
    cost_no_vat = fields.Float("COST (No_Invoice)", readonly=True)
    po_commission_total = fields.Float("COST COM LINE (USD)", readonly=True)
    so_commission_total = fields.Float("COST COM CUS (USD)", readonly=True)
    so_amount_untaxed_vnd = fields.Float("REVENUE Output (No_VAT)", readonly=True)
    so_amount_total_vnd = fields.Float("REVENUE Output (With_VAT)", readonly=True)
    so_amount_tax_vnd = fields.Float("REVENUE Output (VAT)", readonly=True)
    revenue_no_vat = fields.Float("REVENUE (No_Invoice)", readonly=True)

    sum_freehand = fields.Float("Freehand", compute="_compute_sums", readonly=True)
    sum_nominated = fields.Float("Nominated", compute="_compute_sums", readonly=True)
    sum_activities = fields.Float("Sales Activities", compute="_compute_sums", readonly=True)
    sum_all = fields.Float("Total", compute="_compute_sums", readonly=True)

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
        orderby = "incentive_name DESC"
        exchange_rate = int(self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.default_usd_vnd_exchange_rate', -1))
        res = super(SaleIncentiveAnalysisReport, self).read_group(domain, fields, groupby, offset=offset,
                                                                  limit=limit, orderby=orderby, lazy=lazy)
        # Check read_group is on level 1 (grouping by incentive) or level 2 (grouping by salesman)
        is_level_1 = 'incentive_name' in res[0].keys() if len(res) > 0 else False

        fields_to_calculate_total = [   # level 2
            'display_target_sales',
            'sum_freehand',
            'sum_nominated',
            'sum_all',
            'incentive',
            'incentive_tax_amount',
            'incentive_after_tax',
            'display_achieve'
        ]
        if is_level_1:
            fields_to_calculate_total = ['incentive']

        for field in fields_to_calculate_total:
            if field in fields:
                for line in res:
                    if '__domain' in line:
                        records = self.search(line['__domain'])
                        if is_level_1:      # Only column incentive need to calculate
                            total = 0.0
                            if records:
                                # Sort the recordset by the grouping field (here is partner name)
                                # For Many2one fields, you often need to sort by the actual value/name
                                # or the ID if the field is defined with sortable=False
                                sorted_records = records.sorted(key=lambda r: r.display_name if r.display_name else '')

                                # Group using itertools.groupby
                                grouped_items = {}
                                for key, group in itertools.groupby(sorted_records, key=lambda r: r.partner_id):
                                    category_name = key.name if key else 'No Category'
                                    grouped_items[category_name] = list(group)  # Convert group iterator to a list of records

                                for salesman, items in grouped_items.items():
                                    sum_freehand_total = 0.0
                                    sum_nominated_total = 0.0
                                    sum_all_total = 0.0
                                    target_sales_vnd = 0.0
                                    incentive_record = None
                                    if len(items) > 0:
                                        target_sales_vnd = items[0].target_sales * exchange_rate
                                        incentive_record = items[0].incentive_id

                                    for item in items:
                                        sum_freehand_total += item.sum_freehand
                                        sum_nominated_total += item.sum_nominated
                                        sum_all_total += item.sum_all

                                    incentive = self.calculate_incentive_v2(incentive_record, target_sales_vnd,
                                                                            sum_freehand_total, sum_nominated_total,
                                                                            sum_all_total, exchange_rate)
                                    total += incentive
                            line[field] = total

                        else:
                            total = 0.0
                            for record in records:
                                if field == 'display_target_sales':
                                    total = record['target_sales'] * exchange_rate  # Only need first record, no sum
                                    break
                                elif field == 'display_achieve':
                                    break
                                elif field == 'incentive':
                                    incentive_record = records[0].incentive_id if len(records) > 0 else None
                                    target_sales_vnd = line['display_target_sales']
                                    sum_freehand = line['sum_freehand']
                                    sum_nominated = line['sum_nominated']
                                    sum_all = line['sum_all']
                                    incentive = self.calculate_incentive_v2(incentive_record, target_sales_vnd,
                                                                            sum_freehand, sum_nominated, sum_all,
                                                                            exchange_rate)
                                    total = incentive
                                    break
                                elif field == 'incentive_tax_amount':
                                    tax_record = records[0].tax_income_id if len(records) > 0 else None
                                    incentive = line['incentive']
                                    incentive_tax_amount = self.calculate_incentive_tax_amount_v2(tax_record, incentive)
                                    total = incentive_tax_amount
                                    break
                                elif field == 'incentive_after_tax':
                                    incentive = line['incentive']
                                    incentive_tax_amount = line['incentive_tax_amount']
                                    incentive_after_tax = incentive - incentive_tax_amount
                                    total = incentive_after_tax
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

    @api.depends('etd')
    def _compute_format_etd(self):
        for rec in self:
            rec.etd_formatted = ''
            if rec.etd:
                etd_local = self._convert_utc_to_local(rec.etd)
                if etd_local:
                    rec.etd_formatted = etd_local.strftime('%d/%m/%Y')

    def _convert_utc_to_local(self, utc_date):
        result = utc_date
        if result:
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                utc_date_str = utc_date.strftime(fmt)

                ########################################################
                # OPTION 1
                ########################################################
                # now_utc = datetime.now(pytz.timezone('UTC'))
                # tz = pytz.timezone(self.env.user.tz)      # Consider get tz correct
                # now_tz = now_utc.astimezone(tz) or pytz.utc
                # utc_offset_timedelta = datetime.strptime(now_tz.strftime(fmt), fmt) - datetime.strptime(now_utc.strftime(fmt), fmt)
                # # local_date = datetime.strptime(utc_date_str, fmt)
                # result = utc_date + utc_offset_timedelta

                ########################################################
                # OPTION 2
                ########################################################
                timezone = 'UTC'
                if self.env.user.tz:
                    timezone = self.env.user.tz
                elif self.user_id and self.user_id.partner_id.tz:
                    timezone = self.user_id.partner_id.tz
                tz = pytz.timezone(timezone)
                result = pytz.utc.localize(datetime.strptime(utc_date_str, fmt)).astimezone(tz)
            except:
                print("ERROR in _convert_utc_to_local")

            return result

    @api.depends('target_sales')
    def _compute_display_target_sales(self):
        for rec in self:
            rec.display_target_sales = 0

    @api.depends('sum_freehand', 'sum_nominated', 'sum_activities', 'sum_all', 'target_sales')
    def _compute_incentive_and_tax(self):
        # exchange_rate = int(self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.default_usd_vnd_exchange_rate', -1))

        for rec in self:
            # res = self.calculate_incentive_and_tax(rec, exchange_rate)
            # rec.incentive = res['incentive']
            # rec.incentive_tax_amount = res['incentive_tax_amount']
            # rec.incentive_after_tax = res['incentive_after_tax']
            rec.incentive = 0
            rec.incentive_tax_amount = 0
            rec.incentive_after_tax = 0

    @api.depends('so_amount_untaxed', 'po_amount_untaxed', 'margin')
    def _compute_sums(self):
        ''' Business Income Tax - default is 20% if no configuration in system parameters '''
        biz_tax_percentage = float(
            self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.business_income_tax_in_percentage', 20))
        exchange_rate = int(
            self.env['ir.config_parameter'].sudo().get_param('freight_mgmt.default_usd_vnd_exchange_rate', -1))

        biz_income_tax = biz_tax_percentage / 100

        for rec in self:
            sum_freehand = sum_nominated = sum_activities = 0.0

            po_commission_total_vnd = rec.po_commission_total * exchange_rate
            so_commission_total_vnd = rec.so_commission_total * exchange_rate

            real_profit_before_tax = (
                (rec.so_amount_total_vnd + rec.revenue_no_vat) -
                (rec.po_amount_total_vnd + rec.cost_no_vat + po_commission_total_vnd + so_commission_total_vnd)
            )
            untaxed_profit_before_tax = rec.so_amount_untaxed_vnd - rec.po_amount_untaxed_vnd
            vat_payable = rec.so_amount_tax_vnd - rec.po_amount_tax_vnd
            income_tax_amount = untaxed_profit_before_tax * biz_income_tax if untaxed_profit_before_tax > 0 else 0
            final_real_profit_after_tax = real_profit_before_tax - vat_payable - income_tax_amount

            if rec.order_type == 'freehand':
                sum_freehand = final_real_profit_after_tax
            elif rec.order_type == 'nominated':
                sum_nominated = final_real_profit_after_tax

            rec.sum_freehand = sum_freehand
            rec.sum_nominated = sum_nominated
            rec.sum_activities = sum_activities
            rec.sum_all = sum_freehand + sum_nominated + sum_nominated

    @staticmethod
    def calculate_incentive_v2(incentive_record, target_sales_vnd, sum_freehand, sum_nominated, sum_all, exchange_rate_vnd):
        incentive = 0.0

        if incentive_record and incentive_record.section_ids:
            for sec in incentive_record.section_ids:
                amount_from = sec.percent_from * target_sales_vnd / 100
                amount_to = sec.percent_to * target_sales_vnd / 100
                if amount_from <= sum_all < amount_to or target_sales_vnd == 0.0 and amount_from == 0.0:
                    incentive = (sec.incentive_percent_month / 100) * \
                                ((sum_freehand * incentive_record.target_freehand / 100) +
                                 (sum_nominated * incentive_record.target_nominated / 100))
                    break

        return incentive

    @staticmethod
    def calculate_incentive_tax_amount_v2(tax_record, incentive):
        tax_amount = 0.0

        if incentive and tax_record and tax_record.section_ids:
            incentive_tmp = incentive
            if tax_record.tax_income_type == 'section':
                if len(tax_record.section_ids) > 1:
                    sortedDescSections = sorted(tax_record.section_ids, key=lambda x: x.amount_to, reverse=True)
                else:
                    sortedDescSections = tax_record.section_ids

                for sec in sortedDescSections:
                    if sec.amount_from < incentive_tmp <= sec.amount_to:
                        incentive_to_tax = incentive_tmp - sec.amount_from
                        tax_amount += incentive_to_tax * sec.tax_rate_percent / 100
                        incentive_tmp -= incentive_to_tax
            else:  # 'fixed'
                tax_amount = incentive_tmp * tax_record.fix_percent / 100

        return tax_amount

    '''TODO: This method is deprecated'''
    @staticmethod
    def calculate_incentive_and_tax(rec, exchange_rate_vnd):
        incentive = 0.0
        tax_amount = 0.0

        target_sales_vnd = rec.target_sales * exchange_rate_vnd

        if rec.incentive_id and rec.incentive_id.section_ids:
            for sec in rec.incentive_id.section_ids:
                amount_from = sec.percent_from * target_sales_vnd / 100
                amount_to = sec.percent_to * target_sales_vnd / 100
                if amount_from <= rec.sum_all < amount_to or target_sales_vnd == 0.0 and amount_from == 0.0:
                    incentive = (sec.incentive_percent_month / 100) * \
                                ((rec.sum_freehand * rec.incentive_id.target_freehand / 100) +
                                 (rec.sum_nominated * rec.incentive_id.target_nominated / 100) +
                                 (rec.sum_activities * rec.incentive_id.target_activities / 100))
                    break

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
            'incentive_after_tax': incentive - tax_amount
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
                'search_default_filter_etd': 0
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
                'target': 'self',
                'context': context,
                'domain': domain,
            }
        elif len(active_ids) > 1:
            raise UserError("You can only select one record to view details.")
        else:
            raise UserError("Please select a record to view its details.")

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
                
                tblSum.po_amount_untaxed AS po_amount_untaxed,
                tblSum.so_amount_untaxed AS so_amount_untaxed,
                tblSum.margin AS margin,
                
                tblSum.order_type AS order_type,
                tblSum.po_amount_untaxed_vnd AS po_amount_untaxed_vnd,
                tblSum.po_amount_total_vnd AS po_amount_total_vnd,
                tblSum.po_amount_tax_vnd AS po_amount_tax_vnd,
                tblSum.cost_no_vat AS cost_no_vat,
                tblSum.po_commission_total AS po_commission_total,
                tblSum.so_commission_total AS so_commission_total,
                tblSum.so_amount_untaxed_vnd AS so_amount_untaxed_vnd,
                tblSum.so_amount_total_vnd AS so_amount_total_vnd,
                tblSum.so_amount_tax_vnd AS so_amount_tax_vnd,
                tblSum.revenue_no_vat AS revenue_no_vat
        """

        return select_str

    @staticmethod
    def _subquery_profit_forwarder_report():
        # subquery_str = f"""
        #     SELECT id
        #         , user_id
        #         , bill_no
        #         , pod_id
        #         , date_order
        #         , etd
        #         , invoice_date
        #         , payment_state
        #         , CASE WHEN order_type = 'freehand' THEN
        #                 ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
        #                 - (so_amount_tax_vnd - po_amount_tax_vnd)
        #                 - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.2)
        #                 ELSE 0 END as sum_freehand
        #         , CASE WHEN order_type = 'nominated' THEN
        #                 ((so_amount_total_vnd + revenue_no_vat) - (po_amount_total_vnd + cost_no_vat + po_commission_total * 22000 + so_commission_total * 22000))
        #                 - (so_amount_tax_vnd - po_amount_tax_vnd)
        #                 - ((so_amount_untaxed_vnd - po_amount_untaxed_vnd) * 0.2)
        #                 ELSE 0 END as sum_nominated
        #         , 0 as sum_activities
        #     FROM sale_profit_forwarder_analysis_report
        # """

        subquery_str = f"""
            SELECT id
                , user_id
                , bill_no
                , pod_id
                , date_order
                , etd
                , invoice_date
                , payment_state
                , po_amount_untaxed
                , so_amount_untaxed
                , margin
                , order_type
                , po_amount_untaxed_vnd
                , po_amount_total_vnd
                , po_amount_tax_vnd
                , cost_no_vat
                , po_commission_total
                , so_commission_total
                , so_amount_untaxed_vnd
                , so_amount_total_vnd
                , so_amount_tax_vnd
                , revenue_no_vat
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
                incentive_record = None
                tax_record = None
                for incentive in incentives:
                    salesman_sum_freehand_total += incentive.sum_freehand
                    salesman_sum_nominated_total += incentive.sum_nominated
                    # res = SaleIncentiveAnalysisReport.calculate_incentive_and_tax(incentive, exchange_rate)
                    if not incentive_record:
                        incentive_record = incentive.incentive_id    # Take first record because all is same
                    if not tax_record:
                        tax_record = incentive.tax_income_id
                    if display_target_sales == 0.0:
                        display_target_sales = incentive.target_sales * exchange_rate
                    if incentive.etd:
                        month = incentive.etd.strftime('%m')
                        year = incentive.etd.strftime('%Y')
                        if month not in months:
                            months.append(month)
                        if year not in years:
                            years.append(year)

                sum_all = salesman_sum_freehand_total + salesman_sum_nominated_total
                incentive_amount = SaleIncentiveAnalysisReport.calculate_incentive_v2(
                    incentive_record, display_target_sales, salesman_sum_freehand_total,
                    salesman_sum_nominated_total, sum_all, exchange_rate)
                incentive_tax_amount = SaleIncentiveAnalysisReport.calculate_incentive_tax_amount_v2(
                    tax_record, incentive_amount)
                incentive_after_tax = incentive_amount - incentive_tax_amount
                salesman_incentive_after_tax_total += incentive_after_tax

                salesman_sum_revenue_total = salesman_sum_freehand_total + salesman_sum_nominated_total
                achieve = salesman_sum_revenue_total > display_target_sales * 0.5

                incentive_data.append({
                    'sale_name': grouping_salesman,
                    'display_target_sales': display_target_sales,
                    'sum_freehand_total': salesman_sum_freehand_total,
                    'sum_nominated_total': salesman_sum_nominated_total,
                    'sum_revenue_total': salesman_sum_revenue_total,
                    'incentive_before_tax_total': incentive_amount,
                    'incentive_tax_amount': incentive_tax_amount,
                    'incentive_after_tax_total': salesman_incentive_after_tax_total,
                    'achieve': achieve,
                    'incentives': incentives
                })
                total_incentive_type += incentive_amount

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
