# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    allowed_branch_ids = fields.Many2many(string="Allowed Branches", related="employee_id.allowed_branch_ids")
    branch_id = fields.Many2one(string="Default Branch", related="employee_id.branch_id")
