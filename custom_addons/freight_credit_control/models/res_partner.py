# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


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
        # AccountMove = self.env['account.move'].sudo()
        PartnerAgingCustomer = self.env['res.partner.aging.customer'].sudo()
        for partner in self:
            partner.credit_overdue_days = 0
            if not partner.id:
                continue
            commercial_partner = partner.commercial_partner_id or partner
            # overdue_moves = AccountMove.search([
            #     ('commercial_partner_id', '=', commercial_partner.id),
            #     ('move_type', 'in', ('out_invoice', 'out_refund')),
            #     ('state', '=', 'posted'),
            #     ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
            #     ('invoice_date_due', '<', today),
            # ])
            overdue_moves = PartnerAgingCustomer.search([
                ('partner_id', '=', commercial_partner.id),
            ])
            if overdue_moves:
                oldest_due_date = min(overdue_moves.mapped('inv_date_due'))
                partner.credit_overdue_days = (today - oldest_due_date).days

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        try:
            if 'active_limit' in vals or 'blocking_stage' in vals:
                self.env['freight.booking'].sudo().update_credit_hold_state_by_partner(self)
        except Exception as e:
            _logger.exception("Error occurred while updating credit flag: %s" % e)
        return res
