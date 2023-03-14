# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    bio_user_id = fields.Char(string="Bio User ID", tracking=True)
    contract_date_start = fields.Datetime(string="Date Start", tracking=True)
