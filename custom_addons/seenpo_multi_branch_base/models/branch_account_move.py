# -*- coding: utf-8 -*-
#############################################################################
#
#    Bao Thinh Software Ltd.
#
#    Copyright (C) 2023-TODAY Bao Thinh Software(<https://www.baothinh.com>)
#    Author: Bao Thinh Software - Tuan Huynh(<https://www.baothinh.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class AccountMove(models.Model):
    """inherited account move"""
    _inherit = "account.move"

    branch_id = fields.Many2one("res.branch", string='Branch', tracking=True, store=True)

    @api.model
    def _init_default_account_move_branch(self):
        branch_saigon = self.env.ref('seenpo_multi_branch_base.seenpo_branch_saigon')
        invoices = self.search([])
        for invoice in invoices:
            invoice.write({'branch_id': branch_saigon.id})

    # @api.depends('company_id', 'user_id')
    # def _compute_branch_id(self):
    #     for rec in self:
    #         if rec.user_id and rec.user_id.branch_id:
    #             rec.branch_id = rec.user_id.branch_id
    #         else:
    #             rec.branch_id = False


class AccountMoveLine(models.Model):
    """inherited account move line"""
    _inherit = "account.move.line"

    branch_id = fields.Many2one('res.branch', related='move_id.branch_id', string='Branch', store=True)
