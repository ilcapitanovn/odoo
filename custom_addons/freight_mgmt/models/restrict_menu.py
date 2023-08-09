# -*- coding: utf-8 -*-

from odoo import fields, models


class RestrictMenu(models.Model):
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many('res.users')
