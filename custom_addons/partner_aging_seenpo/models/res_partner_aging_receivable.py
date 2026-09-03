# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import date


class ResPartnerAgingReceivable(models.TransientModel):
    _name = 'res.partner.aging.receivable'
    _description = 'Partner Aging Receivable View'

    def open_aging_today(self):
        # Create wizard with default date = today
        wizard = self.env['res.partner.aging.date'].create({
            'age_date': date.today(),
        })

        # Call the original wizard method
        action = wizard.open_customer_aging()

        return action
