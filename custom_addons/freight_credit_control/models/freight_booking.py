# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

CREDIT_HOLD_STATES = [
    ('none', 'Not on Hold'),
    ('blocked', 'Blocked'),
    ('pending_approval', 'Pending Approval'),
    ('released', 'Released'),
]


class FreightBooking(models.Model):
    _inherit = 'freight.booking'

    # ---------------------------------------------------
    # Fields
    # ---------------------------------------------------
    credit_hold_state = fields.Selection(
        CREDIT_HOLD_STATES, string="Credit Status", default='none',
        tracking=True, copy=False, index=True,
        group_expand='_group_expand_credit_hold_state',
        help="Financial hold status of this booking, independent from the "
             "operational Stage. A booking is auto-flagged 'Blocked' when its "
             "customer crosses the Blocking Amount defined on the customer."
    )
    credit_release_note = fields.Text(
        string="Release Note",
        help="Sales' justification when requesting BOD approval to release "
             "this shipment despite the customer's overdue balance."
    )
    credit_reject_reason = fields.Text(string="Rejection Reason")
    credit_requested_by = fields.Many2one('res.users', string="Requested By", copy=False, tracking=True)
    credit_requested_date = fields.Datetime(string="Requested On", copy=False, tracking=True)
    credit_approved_by = fields.Many2one('res.users', string="Approved By", copy=False, tracking=True)
    credit_approved_date = fields.Datetime(string="Approved On", copy=False, tracking=True)

    # Read-only, customer-level credit context surfaced on the booking/card for convenience.
    partner_due_amount = fields.Monetary(
        related='partner_id.total_due_amount', string="Customer Overdue Balance", store=False)
    partner_blocking_stage = fields.Monetary(
        related='partner_id.blocking_stage', string="Blocking Threshold", store=False)
    partner_credit_overdue_days = fields.Integer(
        related='partner_id.credit_overdue_days', string="Days Overdue", store=False)
    is_over_credit_limit = fields.Boolean(
        string="Over Credit Limit", compute='_compute_is_over_credit_limit')

    # ---------------------------------------------------
    # Compute
    # ---------------------------------------------------
    @api.model
    def _group_expand_credit_hold_state(self, states, domain, order):
        """Always show the 3 workflow columns on the Control Tower kanban,
        even when empty. 'none' (bookings never on hold) is left out of the
        board on purpose - it would not be actionable there."""
        return ['blocked', 'pending_approval', 'released']

    @api.depends('partner_id.due_amount', 'partner_id.blocking_stage',
                 'partner_id.active_limit', 'partner_id.enable_credit_limit')
    def _compute_is_over_credit_limit(self):
        for booking in self:
            partner = booking.partner_id
            booking.is_over_credit_limit = bool(
                partner
                and partner.active_limit
                and partner.enable_credit_limit
                and partner.blocking_stage
                and partner.due_amount >= partner.blocking_stage
            )

    # ---------------------------------------------------
    # Workflow actions
    # ---------------------------------------------------
    def action_open_credit_release_wizard(self):
        """Sales requests a BOD approval to release the shipment."""
        self.ensure_one()
        if self.credit_hold_state != 'blocked':
            raise UserError(_("Only a Blocked booking can have a release requested."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Request Credit Release"),
            'res_model': 'freight.credit.release.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id, 'default_wizard_action': 'request'},
        }

    def action_open_credit_reject_wizard(self):
        """BOD rejects a pending release request, with a reason."""
        self.ensure_one()
        if self.credit_hold_state != 'pending_approval':
            raise UserError(_("Only a booking pending approval can be rejected."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Reject Credit Release"),
            'res_model': 'freight.credit.release.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id, 'default_wizard_action': 'reject'},
        }

    def action_approve_credit_release(self):
        """BOD approves a pending release request. Restricted to the
        Credit Approver (BOD) group via the button's `groups` attribute
        in the view, and double-checked here."""
        approver_group = self.env.ref('freight_credit_control.group_freight_credit_approver', raise_if_not_found=False)
        for booking in self:
            if approver_group and approver_group not in self.env.user.groups_id:
                raise UserError(_("Only BOD / Credit Approvers can approve a credit release."))
            if booking.credit_hold_state != 'pending_approval':
                raise UserError(_("Only bookings pending approval can be released. Booking %s is currently '%s'.")
                                 % (booking.number, dict(CREDIT_HOLD_STATES).get(booking.credit_hold_state)))
            booking.write({
                'credit_hold_state': 'released',
                'credit_approved_by': self.env.user.id,
                'credit_approved_date': fields.Datetime.now(),
            })
            booking.message_post(body=_("Credit hold released and approved by %s.") % self.env.user.name)

    def action_print_delivery_order(self):
        """Print the Delivery Order report (bound to freight.billing) for
        this booking's first Bill of Lading, but only if the booking is not
        currently under an un-released financial hold."""
        self.ensure_one()
        if self.is_over_credit_limit and self.credit_hold_state != 'released':
            raise UserError(_(
                "This booking is on financial hold (customer overdue balance %.2f exceeds "
                "the blocking threshold %.2f). Please request BOD approval before printing "
                "the Delivery Order."
            ) % (self.partner_due_amount, self.partner_blocking_stage))
        if not self.billing_id:
            raise UserError(_("There is no Bill of Lading linked to this booking yet."))
        report = self.env.ref('freight_mgmt.freight_delivery_order_report')
        return report.report_action(self.billing_id[0])

    # ---------------------------------------------------
    # Automation
    # ---------------------------------------------------
    def _cron_flag_credit_holds(self):
        """Scheduled action: scan confirmed, not-yet-completed bookings whose
        credit status has never been evaluated ('none') and flag them
        'Blocked' if their customer is over the credit blocking threshold.
        Bookings already Blocked / Pending / Released are left untouched -
        this cron only ever sets the *initial* hold, never overrides a
        BOD decision."""
        candidates = self.search([
            ('confirmed', '=', True),
            ('completed', '=', False),
            ('credit_hold_state', '=', 'none'),
        ])
        to_block = candidates.filtered(lambda b: b.is_over_credit_limit)
        if to_block:
            to_block.write({'credit_hold_state': 'blocked'})
            for booking in to_block:
                booking.message_post(body=_(
                    "This booking has been automatically placed on financial hold: "
                    "customer's overdue balance has crossed the credit blocking threshold."
                ))
        return True
