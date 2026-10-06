# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Number of days since the oldest unpaid/overdue customer invoice became due.
    # Complements base_accounting_kit's `due_amount` (credit - debit) which already
    # gives the outstanding balance but not how long it has been overdue.
    credit_overdue_days = fields.Integer(
        string="Days Overdue",
        compute="_compute_credit_overdue_days",
        help="Number of days since the oldest overdue customer invoice became due."
    )

    def _compute_credit_overdue_days(self):
        today = fields.Date.context_today(self)
        AccountMove = self.env['account.move'].sudo()
        for partner in self:
            partner.credit_overdue_days = 0
            if not partner.id:
                continue
            commercial_partner = partner.commercial_partner_id or partner
            overdue_moves = AccountMove.search([
                ('commercial_partner_id', '=', commercial_partner.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
                ('invoice_date_due', '<', today),
            ])
            if overdue_moves:
                oldest_due_date = min(overdue_moves.mapped('invoice_date_due'))
                partner.credit_overdue_days = (today - oldest_due_date).days
