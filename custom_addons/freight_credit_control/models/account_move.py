# -*- coding: utf-8 -*-

import logging
from odoo import _, models

_logger = logging.getLogger(__name__)


class FreightAccountMove(models.Model):
    _inherit = 'account.move'

    # ---------------------------------------------------
    # Override parent actions
    # ---------------------------------------------------
    def action_update_debit_note_when_invoice_paid(self, record):
        """Override to check if the booking is paid and update the credit_hold_state of
        the booking to 'pending_approval' if it is currently 'none' or 'blocked'."""
        try:
            res = super().action_update_debit_note_when_invoice_paid(record)
            if res:
                related_billing = res.get('related_billing', None)

                if related_billing:
                    is_debit_note_paid = False
                    if record.is_sale_document(include_receipts=True):  # Debit Note
                        is_debit_note_paid = True

                    related_booking = related_billing.booking_id
                    if (is_debit_note_paid and related_booking
                            and related_booking.credit_hold_state in ('none', 'blocked')):
                        # Update credit_hold_state of booking to 'pending_approval' when the payment
                        # is confirmed by accounting
                        related_booking.write({'credit_hold_state': 'pending_approval'})
                        related_booking.message_post(body=_(
                            "This booking has been automatically placed on pending release approval as "
                            "the payment has been confirmed by accounting."
                        ))

        except Exception as e:
            _logger.exception("action_update_debit_note_when_invoice_paid - Exception: %s" % e)
