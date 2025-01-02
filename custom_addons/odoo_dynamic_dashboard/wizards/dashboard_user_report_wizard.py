# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from psycopg2.extensions import AsIs

from odoo import _, api, fields, models, tools


class UserReportWizard(models.TransientModel):
    _name = "dashboard.user.report.wizard"
    _description = "Wizard for reporting users' usage"

    @staticmethod
    def _get_year_selection():
        """Generate year options dynamically."""
        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(2020, current_year + 1)]

    date_year_report = fields.Selection(
        selection=lambda self: self._get_year_selection(),
        string="Report year",
        default=lambda self: str(datetime.now().year)
    )

    def action_generate_report(self):
        self.ensure_one()

        report_year = int(self.date_year_report)
        report_date = datetime(report_year, 1, 1)

        context = {
            'search_default_group_user': 1,
            'search_default_group_date': 1,
            # 'group_by_no_leaf': 1,
            # 'group_by': ['user_id', 'updated_date'],
            'wizard_report_date': report_date
        }

        tools.drop_view_if_exists(self._cr, "dashboard_user_report")
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s )",
            (
                AsIs("dashboard_user_report"),
                AsIs(self._create_general_sql(report_year))
            ),
        )

        # go to results
        res = {
            "name": _("User Report"),
            "type": "ir.actions.act_window",
            "res_model": "dashboard.user.report",
            'view_mode': 'graph,tree,pivot',
            'context': context,
            'target': 'current',
            'search_view_id': [self.env.ref('odoo_dynamic_dashboard.dynamic_dashboard_view_user_analysis_search').id],
        }

        return res

    def _create_general_sql(self, report_year):
        """
        General: list users and dates,
        Discuss: mail_message (with model='mail.channel'),
        Calendar: calendar_event,
        Helpdesk: helpdesk_ticket, helpdesk_ticket_channel, helpdesk_ticket_category, helpdesk_ticket_tag
        Contacts: res_partner,
        Attendances: ,
        CRM: crm_lead,
        Sales: sale_order,
        Products: product_template, product_pricelist,
        Accounting: account_move, account_payment
        Email Marketing: mailing_mailing, mail_activity, mail_mail, mail_message, mail_template
        Purchase: purchase_order,
        Inventory: ,
        Employees: hr_employee, hr_department,
        Time Off: ,
        Freight: ,
        Freight Trading: ,
        Lang Son: ,
        """
        V_USERS = "view_users"
        V_DISCUSS_COUNTS = "view_discuss_counts"
        V_CALENDAR_COUNTS = "view_calendar_counts"

        V_TICKET_COUNTS = "view_ticket_counts"
        V_TICKET_CHANNEL_COUNTS = "view_ticket_channel_counts"
        V_TICKET_CATEGORY_COUNTS = "view_ticket_category_counts"
        V_TICKET_TAG_COUNTS = "view_ticket_tag_counts"

        V_PARTNER_COUNTS = "view_partner_counts"
        V_ATTENDANCES_COUNTS = "view_attendances_counts"
        V_CRM_COUNTS = "view_crm_counts"
        V_SALE_COUNTS = "view_sale_counts"
        V_PRODUCT_COUNTS = "view_product_counts"
        V_PRICELIST_COUNTS = "view_pricelist_counts"
        V_ACCOUNTING_COUNTS = "view_accounting_counts"
        V_ACCOUNTING_PAYMENT_COUNTS = "view_accounting_payment_counts"
        V_FORM_WO_COUNTS = "view_form_wo_counts"
        V_EMAIL_MARKETING_COUNTS = "view_email_marketing_counts"
        V_EMAIL_ACTIVITY_COUNTS = "view_email_activity_counts"
        V_EMAIL_EMAIL_COUNTS = "view_email_email_counts"
        V_EMAIL_MESSAGE_COUNTS = "view_email_message_counts"
        V_EMAIL_TEMPLATE_COUNTS = "view_email_template_counts"
        V_PURCHASE_COUNTS = "view_purchase_counts"
        V_INVENTORY_COUNTS = "view_inventory_counts"
        V_EMPLOYEES_COUNTS = "view_employees_counts"
        V_DEPARTMENT_COUNTS = "view_department_counts"
        V_TIME_OFF_COUNTS = "view_time_off_counts"

        V_BOOKING_COUNTS = "view_booking_counts"
        V_BILLING_COUNTS = "view_billing_counts"
        V_DEBIT_COUNTS = "view_debit_counts"
        V_CREDIT_COUNTS = "view_credit_counts"

        V_TRADING_BOOKING_COUNTS = "view_trading_booking_counts"
        V_TRADING_BILLING_COUNTS = "view_trading_billing_counts"
        V_TRADING_DEBIT_COUNTS = "view_trading_debit_counts"
        V_TRADING_CREDIT_COUNTS = "view_trading_credit_counts"

        V_LANGSON_BOOKING_COUNTS = "view_langson_booking_counts"
        V_LANGSON_BILLING_COUNTS = "view_langson_billing_counts"
        V_LANGSON_DEBIT_COUNTS = "view_langson_debit_counts"
        V_LANGSON_CREDIT_COUNTS = "view_langson_credit_counts"

        A_ID = "id"
        A_USER_ID = "user_id"
        A_LOGIN = "login"
        A_NAME = "display_name"
        A_DATE = "updated_date"
        A_DISCUSS_COUNTS = "alias_total_discusses"
        A_CALENDAR_COUNTS = "alias_total_calendars"

        A_TICKET_COUNTS = "alias_total_tickets"
        A_TICKET_CHANNEL_COUNTS = "alias_total_tickets_channel"
        A_TICKET_CATEGORY_COUNTS = "alias_total_tickets_category"
        A_TICKET_TAG_COUNTS = "alias_total_tickets_tag"

        A_PARTNER_COUNTS = "alias_total_partners"
        A_ATTENDANCES_COUNTS = "alias_total_attendances"
        A_CRM_COUNTS = "alias_total_crms"
        A_SALE_COUNTS = "alias_total_sales"
        A_PRODUCT_COUNTS = "alias_total_products"
        A_PRICELIST_COUNTS = "alias_total_pricelists"
        A_ACCOUNTING_COUNTS = "alias_total_accountings"
        A_ACCOUNTING_PAYMENT_COUNTS = "alias_total_accountings_payment"
        A_FORM_WO_COUNTS = "alias_total_form_wos"
        A_EMAIL_MARKETING_COUNTS = "alias_total_emails"
        A_EMAIL_ACTIVITY_COUNTS = "alias_total_emails_activity"
        A_EMAIL_EMAIL_COUNTS = "alias_total_emails_emails"
        A_EMAIL_MESSAGE_COUNTS = "alias_total_emails_message"
        A_EMAIL_TEMPLATE_COUNTS = "alias_total_emails_template"
        A_PURCHASE_COUNTS = "alias_total_purchases"
        A_INVENTORY_COUNTS = "alias_total_inventory"
        A_EMPLOYEES_COUNTS = "alias_total_employees"
        A_DEPARTMENT_COUNTS = "alias_total_department"
        A_TIME_OFF_COUNTS = "alias_total_time_offs"

        A_BOOKING_COUNTS = "alias_total_bookings"
        A_BILLING_COUNTS = "alias_total_billings"
        A_DEBIT_COUNTS = "alias_total_debits"
        A_CREDIT_COUNTS = "alias_total_credits"
        A_FREIGHT_COUNTS = "alias_total_freight"

        A_TRADING_BOOKING_COUNTS = "alias_total_trading_bookings"
        A_TRADING_BILLING_COUNTS = "alias_total_trading_billings"
        A_TRADING_DEBIT_COUNTS = "alias_total_trading_debits"
        A_TRADING_CREDIT_COUNTS = "alias_total_trading_credits"
        A_TRADING_COUNTS = "alias_total_trading"

        A_LANGSON_BOOKING_COUNTS = "alias_total_langson_bookings"
        A_LANGSON_BILLING_COUNTS = "alias_total_langson_billings"
        A_LANGSON_DEBIT_COUNTS = "alias_total_langson_debits"
        A_LANGSON_CREDIT_COUNTS = "alias_total_langson_credits"
        A_LANGSON_COUNTS = "alias_total_langson"

        """ Sub WHERE conditions """
        S_WHERE_DISCUSS = f" model='mail.channel'"

        """ Define sub-queries sql for views """
        sql_view_users = self._create_sql_view_list_users_dates(V_USERS, report_year, A_USER_ID, A_LOGIN, A_NAME, A_DATE)
        sql_view_discusses = self._create_sql_union_all(V_DISCUSS_COUNTS, A_USER_ID, A_DATE, A_DISCUSS_COUNTS,
                                                        'mail_message', None, S_WHERE_DISCUSS)
        sql_view_calendars = self._create_sql_union_all(V_CALENDAR_COUNTS, A_USER_ID, A_DATE, A_CALENDAR_COUNTS,
                                                        'calendar_event')
        sql_view_tickets = self._create_sql_union_all(V_TICKET_COUNTS, A_USER_ID, A_DATE, A_TICKET_COUNTS,
                                                      'helpdesk_ticket')
        sql_view_tickets_channel = self._create_sql_union_all(V_TICKET_CHANNEL_COUNTS, A_USER_ID, A_DATE,
                                                              A_TICKET_CHANNEL_COUNTS, 'helpdesk_ticket_channel')
        sql_view_tickets_category = self._create_sql_union_all(V_TICKET_CATEGORY_COUNTS, A_USER_ID, A_DATE,
                                                               A_TICKET_CATEGORY_COUNTS, 'helpdesk_ticket_category')
        sql_view_tickets_tag = self._create_sql_union_all(V_TICKET_TAG_COUNTS, A_USER_ID, A_DATE,
                                                          A_TICKET_TAG_COUNTS, 'helpdesk_ticket_tag')
        sql_view_partners = self._create_sql_union_all(V_PARTNER_COUNTS, A_USER_ID, A_DATE, A_PARTNER_COUNTS,
                                                       'res_partner')
        sql_view_attendances = self._create_sql_union_all(V_ATTENDANCES_COUNTS, A_USER_ID, A_DATE, A_ATTENDANCES_COUNTS,
                                                          'seenpo_hr_attendance_bio_log')
        sql_view_crms = self._create_sql_union_all(V_CRM_COUNTS, A_USER_ID, A_DATE, A_CRM_COUNTS, 'crm_lead')
        sql_view_sales = self._create_sql_union_all(V_SALE_COUNTS, A_USER_ID, A_DATE, A_SALE_COUNTS, 'sale_order')
        sql_view_products = self._create_sql_union_all(V_PRODUCT_COUNTS, A_USER_ID, A_DATE, A_PRODUCT_COUNTS,
                                                       'product_template')
        sql_view_pricelists = self._create_sql_union_all(V_PRICELIST_COUNTS, A_USER_ID, A_DATE, A_PRICELIST_COUNTS,
                                                         'product_pricelist')
        sql_view_accountings = self._create_sql_union_all(V_ACCOUNTING_COUNTS, A_USER_ID, A_DATE, A_ACCOUNTING_COUNTS,
                                                          'account_move')
        sql_view_accountings_payment = self._create_sql_union_all(V_ACCOUNTING_PAYMENT_COUNTS, A_USER_ID, A_DATE,
                                                                  A_ACCOUNTING_PAYMENT_COUNTS, 'account_payment')
        sql_view_form_wos = self._create_sql_union_all(V_FORM_WO_COUNTS, A_USER_ID, A_DATE, A_FORM_WO_COUNTS,
                                                       'freight_form_wo')
        sql_view_email_marketing = self._create_sql_union_all(V_EMAIL_MARKETING_COUNTS, A_USER_ID, A_DATE,
                                                              A_EMAIL_MARKETING_COUNTS, 'mailing_mailing')
        sql_view_email_activity = self._create_sql_union_all(V_EMAIL_ACTIVITY_COUNTS, A_USER_ID, A_DATE,
                                                             A_EMAIL_ACTIVITY_COUNTS, 'mail_activity')
        sql_view_email_email = self._create_sql_union_all(V_EMAIL_EMAIL_COUNTS, A_USER_ID, A_DATE,
                                                          A_EMAIL_EMAIL_COUNTS, 'mail_mail')
        sql_view_email_messsage = self._create_sql_union_all(V_EMAIL_MESSAGE_COUNTS, A_USER_ID, A_DATE,
                                                             A_EMAIL_MESSAGE_COUNTS, 'mail_message')
        sql_view_email_template = self._create_sql_union_all(V_EMAIL_TEMPLATE_COUNTS, A_USER_ID, A_DATE,
                                                             A_EMAIL_TEMPLATE_COUNTS, 'mail_template')
        sql_view_purchases = self._create_sql_union_all(V_PURCHASE_COUNTS, A_USER_ID, A_DATE, A_PURCHASE_COUNTS,
                                                        'purchase_order')
        sql_view_inventory = self._create_sql_union_all(V_INVENTORY_COUNTS, A_USER_ID, A_DATE, A_INVENTORY_COUNTS,
                                                        'stock_picking')
        sql_view_employees = self._create_sql_union_all(V_EMPLOYEES_COUNTS, A_USER_ID, A_DATE, A_EMPLOYEES_COUNTS,
                                                        'hr_employee')
        sql_view_department = self._create_sql_union_all(V_DEPARTMENT_COUNTS, A_USER_ID, A_DATE, A_DEPARTMENT_COUNTS,
                                                         'hr_department')
        sql_view_time_offs = self._create_sql_union_all(V_TIME_OFF_COUNTS, A_USER_ID, A_DATE, A_TIME_OFF_COUNTS,
                                                        'hr_leave')

        sql_view_bookings = self._create_sql_union_all(V_BOOKING_COUNTS, A_USER_ID, A_DATE, A_BOOKING_COUNTS,
                                                       'freight_booking', 'SG')
        sql_view_billings = self._create_sql_union_all(V_BILLING_COUNTS, A_USER_ID, A_DATE, A_BILLING_COUNTS,
                                                       'freight_billing', 'SG')
        sql_view_debits = self._create_sql_union_all(V_DEBIT_COUNTS, A_USER_ID, A_DATE, A_DEBIT_COUNTS,
                                                     'freight_debit_note', 'SG')
        sql_view_credits = self._create_sql_union_all(V_CREDIT_COUNTS, A_USER_ID, A_DATE, A_CREDIT_COUNTS,
                                                      'freight_credit_note', 'SG')

        sql_view_tra_bookings = self._create_sql_union_all(V_TRADING_BOOKING_COUNTS, A_USER_ID, A_DATE,
                                                           A_TRADING_BOOKING_COUNTS, 'freight_booking', 'TRA')
        sql_view_tra_billings = self._create_sql_union_all(V_TRADING_BILLING_COUNTS, A_USER_ID, A_DATE,
                                                           A_TRADING_BILLING_COUNTS, 'freight_billing', 'TRA')
        sql_view_tra_debits = self._create_sql_union_all(V_TRADING_DEBIT_COUNTS, A_USER_ID, A_DATE,
                                                         A_TRADING_DEBIT_COUNTS, 'freight_debit_note', 'TRA')
        sql_view_tra_credits = self._create_sql_union_all(V_TRADING_CREDIT_COUNTS, A_USER_ID, A_DATE,
                                                          A_TRADING_CREDIT_COUNTS, 'freight_credit_note', 'TRA')

        sql_view_ls_bookings = self._create_sql_union_all(V_LANGSON_BOOKING_COUNTS, A_USER_ID, A_DATE,
                                                          A_LANGSON_BOOKING_COUNTS, 'freight_booking', 'LS')
        sql_view_ls_billings = self._create_sql_union_all(V_LANGSON_BILLING_COUNTS, A_USER_ID, A_DATE,
                                                          A_LANGSON_BILLING_COUNTS, 'freight_billing', 'LS')
        sql_view_ls_debits = self._create_sql_union_all(V_LANGSON_DEBIT_COUNTS, A_USER_ID, A_DATE,
                                                        A_LANGSON_DEBIT_COUNTS, 'freight_debit_note', 'LS')
        sql_view_ls_credits = self._create_sql_union_all(V_LANGSON_CREDIT_COUNTS, A_USER_ID, A_DATE,
                                                         A_LANGSON_CREDIT_COUNTS, 'freight_credit_note', 'LS')

        general_sql = f"""
                WITH {sql_view_users}, {sql_view_discusses}, {sql_view_calendars}, {sql_view_tickets}
                , {sql_view_tickets_channel}, {sql_view_tickets_category}, {sql_view_tickets_tag}
                , {sql_view_partners}, {sql_view_attendances}, {sql_view_crms}, {sql_view_sales}
                , {sql_view_products}, {sql_view_pricelists}, {sql_view_accountings}, {sql_view_accountings_payment}
                , {sql_view_form_wos}, {sql_view_email_marketing}, {sql_view_email_activity}, {sql_view_email_email}
                , {sql_view_email_messsage}, {sql_view_email_template}, {sql_view_purchases}
                , {sql_view_inventory}, {sql_view_employees}, {sql_view_department}, {sql_view_time_offs}
                , {sql_view_bookings}, {sql_view_billings}, {sql_view_debits}, {sql_view_credits}
                , {sql_view_tra_bookings}, {sql_view_tra_billings}, {sql_view_tra_debits}, {sql_view_tra_credits}
                , {sql_view_ls_bookings}, {sql_view_ls_billings}, {sql_view_ls_debits}, {sql_view_ls_credits}
                SELECT
                    ROW_NUMBER() OVER () AS {A_ID},
                    u.{A_USER_ID},
                    u.{A_LOGIN},
                    u.{A_NAME},
                    CAST(u.{A_DATE} as TIMESTAMP) AS {A_DATE},
                    SUM(COALESCE({A_DISCUSS_COUNTS}, 0)) AS {A_DISCUSS_COUNTS},
                    SUM(COALESCE({A_CALENDAR_COUNTS}, 0)) AS {A_CALENDAR_COUNTS},
                    SUM(COALESCE({A_TICKET_COUNTS}, 0)) + SUM(COALESCE({A_TICKET_CHANNEL_COUNTS}, 0)) + SUM(COALESCE({A_TICKET_CATEGORY_COUNTS}, 0)) + SUM(COALESCE({A_TICKET_TAG_COUNTS}, 0)) AS {A_TICKET_COUNTS},
                    SUM(COALESCE({A_PARTNER_COUNTS}, 0)) AS {A_PARTNER_COUNTS},
                    SUM(COALESCE({A_ATTENDANCES_COUNTS}, 0)) AS {A_ATTENDANCES_COUNTS},
                    SUM(COALESCE({A_CRM_COUNTS}, 0)) AS {A_CRM_COUNTS},
                    SUM(COALESCE({A_SALE_COUNTS}, 0)) AS {A_SALE_COUNTS},
                    SUM(COALESCE({A_PRODUCT_COUNTS}, 0)) + SUM(COALESCE({A_PRICELIST_COUNTS}, 0)) AS {A_PRODUCT_COUNTS},
                    SUM(COALESCE({A_ACCOUNTING_COUNTS}, 0)) + SUM(COALESCE({A_ACCOUNTING_PAYMENT_COUNTS}, 0)) + SUM(COALESCE({A_FORM_WO_COUNTS}, 0)) AS {A_ACCOUNTING_COUNTS},
                    SUM(COALESCE({A_EMAIL_MARKETING_COUNTS}, 0)) AS {A_EMAIL_MARKETING_COUNTS},
                    SUM(COALESCE({A_PURCHASE_COUNTS}, 0)) AS {A_PURCHASE_COUNTS},
                    SUM(COALESCE({A_INVENTORY_COUNTS}, 0)) AS {A_INVENTORY_COUNTS},
                    SUM(COALESCE({A_EMPLOYEES_COUNTS}, 0)) + SUM(COALESCE({A_DEPARTMENT_COUNTS}, 0)) AS {A_EMPLOYEES_COUNTS},
                    SUM(COALESCE({A_TIME_OFF_COUNTS}, 0)) AS {A_TIME_OFF_COUNTS},
                    SUM(COALESCE({A_BOOKING_COUNTS}, 0)) + SUM(COALESCE({A_BILLING_COUNTS}, 0)) + SUM(COALESCE({A_DEBIT_COUNTS}, 0)) + SUM(COALESCE({A_CREDIT_COUNTS}, 0)) AS {A_FREIGHT_COUNTS},
                    SUM(COALESCE({A_TRADING_BOOKING_COUNTS}, 0)) + SUM(COALESCE({A_TRADING_BILLING_COUNTS}, 0)) + SUM(COALESCE({A_TRADING_DEBIT_COUNTS}, 0)) + SUM(COALESCE({A_TRADING_CREDIT_COUNTS}, 0)) AS {A_TRADING_COUNTS},
                    SUM(COALESCE({A_LANGSON_BOOKING_COUNTS}, 0)) + SUM(COALESCE({A_LANGSON_BILLING_COUNTS}, 0)) + SUM(COALESCE({A_LANGSON_DEBIT_COUNTS}, 0)) + SUM(COALESCE({A_LANGSON_CREDIT_COUNTS}, 0)) AS {A_LANGSON_COUNTS}
                FROM
                    {V_USERS} u
                    LEFT JOIN {V_DISCUSS_COUNTS} disc ON u.{A_USER_ID} = disc.{A_USER_ID} AND u.{A_DATE} = disc.{A_DATE}
                    LEFT JOIN {V_CALENDAR_COUNTS} cac ON u.{A_USER_ID} = cac.{A_USER_ID} AND u.{A_DATE} = cac.{A_DATE}
                    LEFT JOIN {V_TICKET_COUNTS} tic ON u.{A_USER_ID} = tic.{A_USER_ID} AND u.{A_DATE} = tic.{A_DATE}
                    LEFT JOIN {V_TICKET_CHANNEL_COUNTS} tichc ON u.{A_USER_ID} = tichc.{A_USER_ID} AND u.{A_DATE} = tichc.{A_DATE}
                    LEFT JOIN {V_TICKET_CATEGORY_COUNTS} ticac ON u.{A_USER_ID} = ticac.{A_USER_ID} AND u.{A_DATE} = ticac.{A_DATE}
                    LEFT JOIN {V_TICKET_TAG_COUNTS} titac ON u.{A_USER_ID} = titac.{A_USER_ID} AND u.{A_DATE} = titac.{A_DATE}
                    LEFT JOIN {V_PARTNER_COUNTS} pc ON u.{A_USER_ID} = pc.{A_USER_ID} AND u.{A_DATE} = pc.{A_DATE}
                    LEFT JOIN {V_ATTENDANCES_COUNTS} atc ON u.{A_USER_ID} = atc.{A_USER_ID} AND u.{A_DATE} = atc.{A_DATE}
                    LEFT JOIN {V_CRM_COUNTS} crmc ON u.{A_USER_ID} = crmc.{A_USER_ID} AND u.{A_DATE} = crmc.{A_DATE}
                    LEFT JOIN {V_SALE_COUNTS} soc ON u.{A_USER_ID} = soc.{A_USER_ID} AND u.{A_DATE} = soc.{A_DATE}
                    LEFT JOIN {V_PRODUCT_COUNTS} proc ON u.{A_USER_ID} = proc.{A_USER_ID} AND u.{A_DATE} = proc.{A_DATE}
                    LEFT JOIN {V_PRICELIST_COUNTS} pric ON u.{A_USER_ID} = pric.{A_USER_ID} AND u.{A_DATE} = pric.{A_DATE}
                    LEFT JOIN {V_ACCOUNTING_COUNTS} acc ON u.{A_USER_ID} = acc.{A_USER_ID} AND u.{A_DATE} = acc.{A_DATE}
                    LEFT JOIN {V_ACCOUNTING_PAYMENT_COUNTS} acpac ON u.{A_USER_ID} = acpac.{A_USER_ID} AND u.{A_DATE} = acpac.{A_DATE}
                    LEFT JOIN {V_FORM_WO_COUNTS} foc ON u.{A_USER_ID} = foc.{A_USER_ID} AND u.{A_DATE} = foc.{A_DATE}
                    LEFT JOIN {V_EMAIL_MARKETING_COUNTS} emc ON u.{A_USER_ID} = emc.{A_USER_ID} AND u.{A_DATE} = emc.{A_DATE}
                    LEFT JOIN {V_PURCHASE_COUNTS} poc ON u.{A_USER_ID} = poc.{A_USER_ID} AND u.{A_DATE} = poc.{A_DATE}
                    LEFT JOIN {V_INVENTORY_COUNTS} inc ON u.{A_USER_ID} = inc.{A_USER_ID} AND u.{A_DATE} = inc.{A_DATE}
                    LEFT JOIN {V_EMPLOYEES_COUNTS} empc ON u.{A_USER_ID} = empc.{A_USER_ID} AND u.{A_DATE} = empc.{A_DATE}
                    LEFT JOIN {V_DEPARTMENT_COUNTS} depc ON u.{A_USER_ID} = depc.{A_USER_ID} AND u.{A_DATE} = depc.{A_DATE}
                    LEFT JOIN {V_TIME_OFF_COUNTS} toc ON u.{A_USER_ID} = toc.{A_USER_ID} AND u.{A_DATE} = toc.{A_DATE}
                    LEFT JOIN {V_BOOKING_COUNTS} bkc ON u.{A_USER_ID} = bkc.{A_USER_ID} AND u.{A_DATE} = bkc.{A_DATE}
                    LEFT JOIN {V_BILLING_COUNTS} blc ON u.{A_USER_ID} = blc.{A_USER_ID} AND u.{A_DATE} = blc.{A_DATE}
                    LEFT JOIN {V_DEBIT_COUNTS} dnc ON u.{A_USER_ID} = dnc.{A_USER_ID} AND u.{A_DATE} = dnc.{A_DATE}
                    LEFT JOIN {V_CREDIT_COUNTS} cnc ON u.{A_USER_ID} = cnc.{A_USER_ID} AND u.{A_DATE} = cnc.{A_DATE}
                    LEFT JOIN {V_TRADING_BOOKING_COUNTS} tbkc ON u.{A_USER_ID} = tbkc.{A_USER_ID} AND u.{A_DATE} = tbkc.{A_DATE}
                    LEFT JOIN {V_TRADING_BILLING_COUNTS} tblc ON u.{A_USER_ID} = tblc.{A_USER_ID} AND u.{A_DATE} = tblc.{A_DATE}
                    LEFT JOIN {V_TRADING_DEBIT_COUNTS} tdnc ON u.{A_USER_ID} = tdnc.{A_USER_ID} AND u.{A_DATE} = tdnc.{A_DATE}
                    LEFT JOIN {V_TRADING_CREDIT_COUNTS} tcnc ON u.{A_USER_ID} = tcnc.{A_USER_ID} AND u.{A_DATE} = tcnc.{A_DATE}
                    LEFT JOIN {V_LANGSON_BOOKING_COUNTS} lbkc ON u.{A_USER_ID} = lbkc.{A_USER_ID} AND u.{A_DATE} = lbkc.{A_DATE}
                    LEFT JOIN {V_LANGSON_BILLING_COUNTS} lblc ON u.{A_USER_ID} = lblc.{A_USER_ID} AND u.{A_DATE} = lblc.{A_DATE}
                    LEFT JOIN {V_LANGSON_DEBIT_COUNTS} ldnc ON u.{A_USER_ID} = ldnc.{A_USER_ID} AND u.{A_DATE} = ldnc.{A_DATE}
                    LEFT JOIN {V_LANGSON_CREDIT_COUNTS} lcnc ON u.{A_USER_ID} = lcnc.{A_USER_ID} AND u.{A_DATE} = lcnc.{A_DATE}
                WHERE
                    COALESCE({A_CALENDAR_COUNTS}, 0) + COALESCE({A_TICKET_COUNTS}, 0) + COALESCE({A_TICKET_CHANNEL_COUNTS}, 0) 
                    + COALESCE({A_TICKET_CATEGORY_COUNTS}, 0)+ COALESCE({A_TICKET_TAG_COUNTS}, 0)  + COALESCE({A_PARTNER_COUNTS}, 0)
                    + COALESCE({A_ATTENDANCES_COUNTS}, 0) + COALESCE({A_CRM_COUNTS}, 0) + COALESCE({A_SALE_COUNTS}, 0) 
                    + COALESCE({A_PRODUCT_COUNTS}, 0) + COALESCE({A_PRICELIST_COUNTS}, 0)
                    + COALESCE({A_ACCOUNTING_COUNTS}, 0) + COALESCE({A_ACCOUNTING_PAYMENT_COUNTS}, 0) + COALESCE({A_FORM_WO_COUNTS}, 0)
                    + COALESCE({A_EMAIL_MARKETING_COUNTS}, 0) + COALESCE({A_PURCHASE_COUNTS}, 0)
                    + COALESCE({A_INVENTORY_COUNTS}, 0) + COALESCE({A_EMPLOYEES_COUNTS}, 0) + COALESCE({A_DEPARTMENT_COUNTS}, 0)
                    + COALESCE({A_TIME_OFF_COUNTS}, 0)
                    + COALESCE({A_BOOKING_COUNTS}, 0) + COALESCE({A_BILLING_COUNTS}, 0)
                    + COALESCE({A_DEBIT_COUNTS}, 0) + COALESCE({A_CREDIT_COUNTS}, 0)
                    + COALESCE({A_TRADING_BOOKING_COUNTS}, 0) + COALESCE({A_TRADING_BILLING_COUNTS}, 0)
                    + COALESCE({A_TRADING_DEBIT_COUNTS}, 0) + COALESCE({A_TRADING_CREDIT_COUNTS}, 0)
                    + COALESCE({A_LANGSON_BOOKING_COUNTS}, 0) + COALESCE({A_LANGSON_BILLING_COUNTS}, 0)
                    + COALESCE({A_LANGSON_DEBIT_COUNTS}, 0) + COALESCE({A_LANGSON_CREDIT_COUNTS}, 0)
                    > 0 
                GROUP BY
                    u.{A_USER_ID}, u.{A_LOGIN}, u.{A_NAME}, u.{A_DATE}
                ORDER BY
                    u.{A_DATE}
            """
        return general_sql

    @staticmethod
    def _create_sql_view_list_users_dates(view_name, report_year, alias_user_id, alias_login, alias_name, alias_updated_date):
        today = datetime.now()
        start_date = datetime(report_year, 1, 1)
        end_date = datetime(report_year, 12, 31)
        if today.year == report_year:
            end_date = datetime(report_year, today.month, today.day)

        sql_list_users = f"""
                {view_name} AS (
                    SELECT
                        ru.id AS {alias_user_id},
                        ru.login AS {alias_login},
                        he.name AS {alias_name},
                        gs.date AS {alias_updated_date}
                    FROM
                        res_users ru
                        CROSS JOIN
                            generate_series (DATE('{start_date}'), DATE('{end_date}'), '1 day') AS gs
                        INNER JOIN
                            hr_employee he ON ru.id = he.user_id
                    WHERE
						ru.login NOT IN ('noreply@viet-toan.com', 'hat726@gmail.com', 'bruceleelht@gmail.com', 'luchuynh005@gmail.com')
                )
            """
        return sql_list_users

    def _create_sql_union_all(self, view_name, alias_user_id, alias_updated_date, alias_count,
                              table_name_of_model, branch_code='', sub_where_conditions=''):
        report_year = int(self.date_year_report)
        create_date_counts = self._create_sql_view_count_create_date(report_year, alias_user_id, alias_updated_date,
                                                                     alias_count, table_name_of_model, branch_code,
                                                                     sub_where_conditions)
        write_date_counts = self._create_sql_view_count_write_date(report_year, alias_user_id, alias_updated_date,
                                                                   alias_count, table_name_of_model, branch_code,
                                                                   sub_where_conditions)
        record_counts = """
                %s AS (%s UNION ALL %s)
            """ % (view_name, create_date_counts, write_date_counts)
        return record_counts

    @staticmethod
    def _create_sql_view_count_create_date(report_year, alias_user_id, alias_updated_date, alias_count,
                                           table_name_of_model, branch_code='', sub_where_conditions=''):
        sub_where = ''
        if branch_code:
            sub_where += f" AND branch_id IN (SELECT id FROM res_branch WHERE code = '{branch_code}')"
        if sub_where_conditions:
            sub_where += f" AND {sub_where_conditions}"

        record_counts = f"""
                SELECT
                    create_uid AS {alias_user_id},
                    DATE(create_date) AS {alias_updated_date},
                    COUNT(*) AS {alias_count}
                FROM
                    {table_name_of_model}
                WHERE
                    DATE_PART('year', create_date) = {report_year}
                    {sub_where}
                GROUP BY
                    create_uid, DATE(create_date)
            """
        return record_counts

    @staticmethod
    def _create_sql_view_count_write_date(report_year, alias_user_id, alias_updated_date, alias_count,
                                          table_name_of_model, branch_code='', sub_where_conditions=''):
        sub_where = ''
        if branch_code:
            sub_where += f" AND branch_id IN (SELECT id FROM res_branch WHERE code = '{branch_code}')"
        if sub_where_conditions:
            sub_where += f" AND {sub_where_conditions}"

        record_counts = f"""
                SELECT
                    write_uid AS {alias_user_id},
                    DATE(write_date) AS {alias_updated_date},
                    COUNT(*) AS {alias_count}
                FROM
                    {table_name_of_model}
                WHERE
                    DATE_PART('year', write_date) = {report_year} AND create_date != write_date
                    {sub_where}
                GROUP BY
                    write_uid, DATE(write_date)
            """
        return record_counts
