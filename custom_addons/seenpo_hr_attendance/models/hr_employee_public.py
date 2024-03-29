# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    bio_user_id = fields.Char(string="Bio User ID", related="employee_id.bio_user_id")
    contract_date_start = fields.Datetime(string="Date Start", related="employee_id.contract_date_start")
