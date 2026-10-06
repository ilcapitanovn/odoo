# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class FreightCreditReleaseWizard(models.TransientModel):
    _name = 'freight.credit.release.wizard'
    _description = 'Freight Credit Release / Reject Wizard'

    booking_id = fields.Many2one('freight.booking', string="Booking", required=True)
    wizard_action = fields.Selection([
        ('request', 'Request Approval'),
        ('reject', 'Reject'),
    ], string="Action", required=True, default='request')
    note = fields.Text(string="Note / Reason", required=True)

    # Read-only context shown in the wizard so the requester/approver has the
    # numbers in front of them without leaving the popup.
    partner_id = fields.Many2one(related='booking_id.partner_id', string="Customer", readonly=True)
    partner_due_amount = fields.Monetary(related='booking_id.partner_due_amount', currency_field='currency_id', readonly=True)
    partner_credit_overdue_days = fields.Integer(related='booking_id.partner_credit_overdue_days', readonly=True)

    currency_id = fields.Many2one('res.currency', string='Currency', related='booking_id.currency_id')

    def action_confirm(self):
        self.ensure_one()
        booking = self.booking_id
        if self.wizard_action == 'request':
            booking.write({
                'credit_hold_state': 'pending_approval',
                'credit_release_note': self.note,
                'credit_requested_by': self.env.user.id,
                'credit_requested_date': fields.Datetime.now(),
            })
            booking.message_post(body=_("Credit release requested by %s: %s") % (self.env.user.name, self.note))

            approver_group = self.env.ref('freight_credit_control.group_freight_credit_approver', raise_if_not_found=False)
            if approver_group:
                for user in approver_group.users:
                    booking.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Credit release approval needed - %s') % booking.number,
                        note=self.note,
                        user_id=user.id,
                    )
        else:
            booking.write({
                'credit_hold_state': 'blocked',
                'credit_reject_reason': self.note,
            })
            booking.message_post(body=_("Credit release rejected by %s: %s") % (self.env.user.name, self.note))
        return {'type': 'ir.actions.act_window_close'}
