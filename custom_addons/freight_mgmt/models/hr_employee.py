# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    allowed_branch_ids = fields.Many2many(string="Allowed Branches", related="user_id.branch_ids", readonly=False)
    branch_id = fields.Many2one(string="Default Branch", related="user_id.branch_id", readonly=False)
