# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import date
from dateutil.relativedelta import relativedelta


class ResPartnerAgingSupplier(models.Model):
    _inherit = 'res.partner.aging.supplier'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='invoice_id.currency_id',
        readonly=True
    )
