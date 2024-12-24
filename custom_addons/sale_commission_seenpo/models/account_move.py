# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


class AccountMoveLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"
    _description = "Agent detail of commission line in account invoice lines"

    amount_custom = fields.Float(string="Commission Amount Custom", default=0.0,
                                 store=True, tracking=True)
