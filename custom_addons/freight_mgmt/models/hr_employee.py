# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    allowed_branch_ids = fields.Many2many(string="Allowed Branches", related="user_id.branch_ids", readonly=False, tracking=True)
    branch_id = fields.Many2one(string="Default Branch", related="user_id.branch_id", readonly=False, tracking=True)


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    department_id = fields.Many2one('hr.department', tracking=True)
    parent_id = fields.Many2one('hr.employee', tracking=True)
    coach_id = fields.Many2one('hr.employee', tracking=True)
    work_phone = fields.Char(tracking=True)
    mobile_phone = fields.Char(tracking=True)
    work_email = fields.Char(tracking=True)
    work_location_id = fields.Many2one('hr.work.location', tracking=True)
    leave_manager_id = fields.Many2one('res.users', tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar', tracking=True)
