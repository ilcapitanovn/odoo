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
        CREDIT_HOLD_STATES, string="Hold Status", default='none',
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

    credit_hold_reason = fields.Selection(
        selection=[
            ('overdue_debt', 'Overdue Debt'),
            ('payment_received', 'Payment Received'),
            ('waiting_payment', 'Waiting Payment'),
            ('financial_hold', 'Financial Hold'),
            ('manager_review', 'Manager Review'),
            ('other', 'Other')
        ],
        string="Hold Reason", default='other',
        compute="_compute_credit_hold_reason",
        help="Indicates why this booking has been placed on financial hold.",
        store=False, readonly=True
    )

    # Read-only, customer-level credit context surfaced on the booking/card for convenience.
    partner_due_amount = fields.Monetary(
        related='partner_id.total_due_amount', string="Customer Overdue Balance", store=False)
    partner_blocking_stage = fields.Monetary(
        related='partner_id.blocking_stage', string="Blocking Threshold", store=False)
    partner_credit_overdue_days = fields.Integer(
        related='partner_id.credit_overdue_days', string="Days Overdue", store=False)
    is_over_credit_limit = fields.Boolean(
        string="Over Credit Limit", compute='_compute_is_over_credit_limit')
    is_within_credit_limit = fields.Boolean(
        string="Within Credit Limit", compute='_compute_is_within_credit_limit')
    booking_due_amount = fields.Monetary(
        string="Overdue Balance", compute='_compute_booking_due_aging_customer', store=False)
    booking_due_days = fields.Integer(
        string="Days Overdue", compute='_compute_booking_due_aging_customer', store=False)

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

    @api.depends('partner_id.due_amount', 'partner_id.blocking_stage',
                 'partner_id.active_limit', 'partner_id.enable_credit_limit')
    def _compute_is_within_credit_limit(self):
        for booking in self:
            partner = booking.partner_id
            booking.is_within_credit_limit = bool(
                partner
                and partner.active_limit
                and partner.enable_credit_limit
                and partner.blocking_stage
                and partner.due_amount < partner.blocking_stage
            )

    def _compute_booking_due_aging_customer(self):
        """Compute the overdue balance and days overdue for this booking's
        customer, based on the res.partner.aging.customer model."""
        customer_aging = self.env['res.partner.aging.customer'].sudo().search([('total', '>', 0)])
        for rec in self:
            rec.booking_due_amount = 0.0
            rec.booking_due_days = 0
            if not rec.id or not customer_aging or len(customer_aging) == 0 or not rec.vessel_bol_no:
                continue

            matching_recs = customer_aging.filtered(lambda ca: ca.bl_number == rec.vessel_bol_no)
            if not matching_recs:
                continue

            rec.booking_due_amount = sum(matching_recs.mapped("total"))
            rec.booking_due_days = max(matching_recs.mapped("max_days_overdue"))

    @api.depends('credit_hold_state', 'is_over_credit_limit', 'order_id.payment_state')
    def _compute_credit_hold_reason(self):
        for rec in self:
            reason = 'other'

            if rec.credit_hold_state == 'blocked':
                if rec.booking_due_days > 0:
                    reason = 'overdue_debt'
                elif rec.booking_due_days == 0 and rec.order_id and rec.order_id.payment_state != 'paid':
                    reason = 'waiting_payment'
                else:
                    reason = 'financial_hold'

            elif rec.credit_hold_state == 'pending_approval':
                if rec.booking_due_days > 0:
                    reason = 'manager_review'
                elif rec.booking_due_days == 0 and rec.order_id and rec.order_id.payment_state == 'paid':
                    reason = 'payment_received'
                elif rec.booking_due_days == 0 and rec.order_id and rec.order_id.payment_state != 'paid':
                    reason = 'manager_review'
                else:
                    reason = 'other'

            rec.credit_hold_reason = reason

    def _send_credit_mail(self, xmlid, partners):
        template = self.env.ref('freight_credit_control.' + xmlid, raise_if_not_found=False)
        partners = partners.filtered('email')
        if not template or not partners:
            return
        for booking in self:
            template.send_mail(
                booking.id, force_send=False,
                email_values={'recipient_ids': [(6, 0, partners.ids)], 'email_to': False})

    def _credit_requester_partners(self):
        self.ensure_one()
        return (self.credit_requested_by | self.user_id).partner_id

    # ---------------------------------------------------
    # Override parent actions
    # ---------------------------------------------------
    def action_confirm(self):
        res = super().action_confirm()

        for booking in self:
            if (booking.confirmed
                    and booking.credit_hold_state == 'none'
                    and not booking.is_within_credit_limit):
                booking.write({'credit_hold_state': 'blocked'})
                booking.message_post(body=_(
                    "This booking has been automatically placed on financial hold: "
                    "customer's overdue balance has crossed the credit blocking threshold."
                ))
        return res

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
        approver_group = self.env.ref('freight_mgmt.group_freight_manager', raise_if_not_found=False)
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
            booking._send_credit_mail('freight_mail_template_credit_release_approved',
                                      booking._credit_requester_partners())
        # Same reasoning as the wizard's action_confirm: this button changes
        # credit_hold_state, which moves the card to a different Kanban
        # column. Odoo's kanban controller only patches the clicked record's
        # fields in place on a type="object" button click - it never
        # re-groups the board - so force a client-side reload instead.
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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
    # CRUD
    # ---------------------------------------------------
    def write(self, vals):
        if 'credit_hold_state' in vals:
            has_manager_group = self.env.user.has_group('freight_mgmt.group_freight_manager')

            # Allow system/superuser automated processes (e.g., cron or sudo) if needed
            if not has_manager_group and not self.env.is_superuser():
                raise UserError(_("Only Freight Administrators can manually update the Hold Status."))

        return super().write(vals)

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
            ('stage_id.name', 'not in', ('Draft', 'Cancelled')),
            ('credit_hold_state', '=', 'none'),
            ('order_id.payment_state', 'not in', ('paid', 'in_payment', 'reversed'))
        ], limit=300)

        """ Block any booking confirmed and unpaid unless its customer is within the credit limit.
        This is a more useful filter than the original, which blocked any booking whose customer was
        over the credit limit or having overdue invoices."""
        to_block = candidates.filtered(lambda b: not b.is_within_credit_limit)
        if to_block:
            to_block.write({'credit_hold_state': 'blocked'})
            for booking in to_block:
                booking.message_post(body=_(
                    "This booking has been automatically placed on financial hold: "
                    "customer's overdue balance has crossed the credit blocking threshold."
                ))

        return True

    def manual_action_flag_credit_holds_release(self):
        # TODO: Implement the logic for manually releasing credit holds. Delete after released to Production
        candidates = self.search([
            ('stage_id.name', 'not in', ('Draft', 'Cancelled')),
            ('credit_hold_state', '!=', 'released'),
            ('order_id.payment_state', 'in', ('paid', 'in_payment'))
        ])
        if candidates:
            candidates.write({'credit_hold_state': 'released'})
            for booking in candidates:
                booking.message_post(body=_(
                    "This booking has been automatically marked as released as the payment "
                    "has been confirmed by accounting."
                ))

    def manual_action_flag_unblocked_credit(self):
        # TODO: Implement the logic for manually unblocking credit holds. Delete after released to Production
        candidates = self.search([
            ('credit_hold_state', '=', 'blocked'),
            ('partner_id.active_limit', '=', True),
            ('partner_id.enable_credit_limit', '=', True)
        ])
        to_unblock = candidates.filtered(lambda b: b.is_within_credit_limit)
        if to_unblock:
            to_unblock.write({'credit_hold_state': 'none'})
            for booking in to_unblock:
                booking.message_post(body=_(
                    "This booking has been automatically marked as unblocked as the customer's "
                    "credit status has been updated."
                ))
