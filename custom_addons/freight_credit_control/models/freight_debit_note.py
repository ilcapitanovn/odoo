# -*- coding: utf-8 -*-

from odoo import _, models


class FreightDebitNote(models.Model):
    _inherit = 'freight.debit.note'

    # ---------------------------------------------------
    # Override parent actions
    # ---------------------------------------------------
    def action_confirm(self):
        self.ensure_one()
        res = super().action_confirm()

        booking = self.booking_id
        if booking and booking.credit_hold_state == 'none':
            booking.write({'credit_hold_state': 'blocked'})
            booking.message_post(body=_(
                "This booking has been automatically placed on financial hold: "
                "waiting for payment before proceeding."
            ))

        return res
