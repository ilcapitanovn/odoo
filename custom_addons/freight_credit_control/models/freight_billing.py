# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import UserError


class FreightBilling(models.Model):
    _inherit = 'freight.billing'

    # ---------------------------------------------------
    # Override parent actions
    # ---------------------------------------------------
    def action_confirm(self):
        """Override to check if the booking is on credit hold before confirming the billing."""
        for billing in self:
            booking = billing.booking_id
            on_hold = (
                    booking.credit_hold_state in ('blocked', 'pending_approval')
                    or (booking.credit_hold_state == 'none' and booking.is_over_credit_limit)
            )
            if on_hold:
                raise UserError(_(
                    "Booking %s is on financial hold (customer overdue balance $%.2f exceeds the blocking threshold"
                    " $%.2f). Please request BOD approval before confirming the Bill of Lading."
                ) % (booking.number, booking.partner_due_amount, booking.partner_blocking_stage))
        return super(FreightBilling, self).action_confirm()
