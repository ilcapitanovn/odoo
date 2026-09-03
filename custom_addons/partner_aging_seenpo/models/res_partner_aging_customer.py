# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import date
from dateutil.relativedelta import relativedelta


class ResPartnerAgingCustomer(models.Model):
    _inherit = 'res.partner.aging.customer'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='invoice_id.currency_id',
        readonly=True
    )

    total = fields.Float(group_operator="sum")
    days_due_01to30 = fields.Float(group_operator="sum")
    days_due_31to60 = fields.Float(group_operator="sum")
    days_due_61to90 = fields.Float(group_operator="sum")
    days_due_91to120 = fields.Float(group_operator="sum")
    days_due_121togr = fields.Float(group_operator="sum")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # age_date = self._context.get('age_date')
        filter_flag = self._context.get('aging_filter')

        # Default: today
        age_date = date.today()

        if filter_flag == 'end_last_month':
            age_date = date.today().replace(day=1) - relativedelta(days=1)

        elif filter_flag == 'end_last_year':
            age_date = date.today().replace(month=1, day=1) - relativedelta(days=1)

        if age_date:
            self.execute_aging_query(age_date=age_date)
        return super().search(args, offset=offset, limit=limit, order=order, count=count)
