# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import html_keep_url

from datetime import date, timedelta
from collections import defaultdict

class FreightBilling(models.Model):
    _name = "freight.billing"
    _description = "Freight Billing"
    _rec_name = "name"
    _order = "name desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin"]

    @api.model
    def _default_note(self):
        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        if use_invoice_terms and self.env.company.terms_type == "html":
            baseurl = html_keep_url(self._default_note_url() + '/terms')
            return _('Terms & Conditions: %s', baseurl)
        return use_invoice_terms and self.env.company.invoice_terms or ''

    def _default_billing_number(self):
        seq = self.env["ir.sequence"]
        # if "company_id" in values:
        #     seq = seq.with_company(values["company_id"])
        return seq.next_by_code("freight.billing.sequence") or "Draft"

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    # ==== Business fields ====
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    # number = fields.Char(string="Bill number")
    name = fields.Char(string='Bill Number', copy=False, readonly=False, store=True, index=True,
                       tracking=True, required=True, default=_default_billing_number)
    bill_ref = fields.Char(string="Bill reference")
    description = fields.Char(translate=True)

    shipper_id = fields.Many2one(comodel_name="res.partner",
                                 domain=[("category_id.name", "=", "Shipper")],
                                 string="Shipper")
    shipper_name = fields.Char()
    shipper_email = fields.Char(string="Shipper's Email")
    shipper_address = fields.Char(string="Shipper's Address")

    consignee_id = fields.Many2one(comodel_name="res.partner",
                                   domain=[("category_id.name", "=", "Consignee")],
                                   string="Consignee")
    consignee_name = fields.Char()
    consignee_email = fields.Char(string="Consignee's Email")
    consignee_address = fields.Char(string="Consignee's Address")

    party_id = fields.Many2one(comodel_name="res.partner", string="Party Notification")
    party_name = fields.Char()
    party_email = fields.Char(string="Party's Email")
    party_address = fields.Char(string="Party's Address")

    contact_id = fields.Many2one(comodel_name="res.partner", string="Delivery Contact")
    contact_name = fields.Char()
    contact_email = fields.Char(string="Contact's Email")
    contact_address = fields.Char(string="Contact's Address")

    note = fields.Html('Terms and conditions', default=_default_note)

    booking_id = fields.Many2one(
        comodel_name="freight.booking", string="Booking", tracking=True, index=True
    )
    port_loading_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Port of loading", tracking=True, index=True
    )
    port_discharge_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Port of discharge", tracking=True, index=True
    )
    vessel_id = fields.Many2one(
        comodel_name="freight.catalog.vessel", string="Ocean vessel", tracking=True, index=True
    )
    pre_carriage = fields.Char(string="Pre-carriage by")
    delivery_place = fields.Char(string="Place of delivery")
    final_destination = fields.Char(string="Final destination")

    billing_line = fields.One2many('freight.billing.line', 'billing_id', string='Billing Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 auto_join=True)

    total_packages_word = fields.Char(string="Total Packs (in word)")
    freight_charge_rate = fields.Char(string="Charge types")
    rated_as = fields.Char(string="Rated as")
    payment_place = fields.Char(string="Place of payment")
    issue_type = fields.Char(string="Type of issue")
    movement_type = fields.Char(string="Type of movement")
    payable_at = fields.Char(string="Payable at")

    bill_date = fields.Datetime(string="Bill Date", default=fields.Datetime.now)
    due_date = fields.Datetime(string="Due Date")

    user_id = fields.Many2one(
        comodel_name="res.users", string="Assigned user", tracking=True, index=True
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    sequence = fields.Integer(default=16)

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, tracking=True, default='draft', group_expand='_expand_states')

    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked")
        ],
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self:
            # res.append((rec.id, rec.number + " - " + rec.name))
            res.append((rec.id, rec.name))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})



    # @api.depends('state', 'date')
    # def _compute_name(self):
    #     def journal_key(move):
    #         return (move.journal_id, move.journal_id.refund_sequence and move.move_type)
    #
    #     def date_key(move):
    #         return (move.date.year, move.date.month)
    #
    #     grouped = defaultdict(  # key: journal_id, move_type
    #         lambda: defaultdict(  # key: first adjacent (date.year, date.month)
    #             lambda: {
    #                 'records': self.env['account.move'],
    #                 'format': False,
    #                 'format_values': False,
    #                 'reset': False
    #             }
    #         )
    #     )
    #     self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
    #     highest_name = self[0]._get_last_sequence() if self else False
    #
    #     # Group the moves by journal and month
    #     for move in self:
    #         if not highest_name and move == self[0] and move.date:
    #             # In the form view, we need to compute a default sequence so that the user can edit
    #             # it. We only check the first move as an approximation (enough for new in form view)
    #             pass
    #         elif (move.name and move.name != '/') or move.state != 'posted':
    #             try:
    #                 # if not move.posted_before:
    #                 move._constrains_date_sequence()
    #                 # Has already a name or is not posted, we don't add to a batch
    #                 continue
    #             except ValidationError:
    #                 # Has never been posted and the name doesn't match the date: recompute it
    #                 pass
    #         group = grouped[journal_key(move)][date_key(move)]
    #         if not group['records']:
    #             # Compute all the values needed to sequence this whole group
    #             move._set_next_sequence()
    #             group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
    #             group['reset'] = move._deduce_sequence_number_reset(move.name)
    #         group['records'] += move
    #
    #     # Fusion the groups depending on the sequence reset and the format used because `seq` is
    #     # the same counter for multiple groups that might be spread in multiple months.
    #     final_batches = []
    #     for journal_group in grouped.values():
    #         journal_group_changed = True
    #         for date_group in journal_group.values():
    #             if (
    #                     journal_group_changed
    #                     or final_batches[-1]['format'] != date_group['format']
    #                     or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
    #             ):
    #                 final_batches += [date_group]
    #                 journal_group_changed = False
    #             elif date_group['reset'] == 'never':
    #                 final_batches[-1]['records'] += date_group['records']
    #             elif (
    #                     date_group['reset'] == 'year'
    #                     and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
    #             ):
    #                 final_batches[-1]['records'] += date_group['records']
    #             else:
    #                 final_batches += [date_group]
    #
    #     # Give the name based on previously computed values
    #     for batch in final_batches:
    #         for move in batch['records']:
    #             move.name = batch['format'].format(**batch['format_values'])
    #             batch['format_values']['seq'] += 1
    #         batch['records']._compute_split_sequence()
    #
    #     self.filtered(lambda m: not m.name).name = '/'

    def _get_starting_sequence(self):
        self.ensure_one()
        # if self.journal_id.type == 'sale':
        #     starting_sequence = "%s/%04d/00000" % (self.journal_id.code, self.date.year)
        # else:
        starting_sequence = "%s/%04d/%02d/0000" % ("VITOSGN", self.date.year, self.date.month)
        # if self.journal_id.refund_sequence and self.move_type in ('out_refund', 'in_refund'):
        #     starting_sequence = "R" + starting_sequence
        return starting_sequence

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in type(self).state.selection]

    @api.onchange("booking_id")
    def _onchange_booking_id(self):
        if self.booking_id:
            self.port_loading_id = self.booking_id.port_loading_id
            self.port_discharge_id = self.booking_id.port_discharge_id
            self.vessel_id = self.booking_id.vessel_id

    @api.onchange("shipper_id")
    def _onchange_shipper_id(self):
        if self.shipper_id:
            self.shipper_name = self.shipper_id.name
            self.shipper_email = self.shipper_id.email
            self.shipper_address = self.shipper_id.contact_address

    @api.onchange("consignee_id")
    def _onchange_consignee_id(self):
        if self.consignee_id:
            self.consignee_name = self.consignee_id.name
            self.consignee_email = self.consignee_id.email
            self.consignee_address = self.consignee_id.contact_address

    @api.onchange("party_id")
    def _onchange_party_id(self):
        if self.party_id:
            self.party_name = self.party_id.name
            self.party_email = self.party_id.email
            self.party_address = self.party_id.contact_address

    @api.onchange("contact_id")
    def _onchange_contact_id(self):
        if self.contact_id:
            self.contact_name = self.contact_id.name
            self.contact_email = self.contact_id.email
            self.contact_address = self.contact_id.contact_address

    # @api.onchange("user_id")
    # def _onchange_dominion_user_id(self):
    #     if self.user_id: # and self.user_ids:
    #         self.update({"user_id": False})
    #         return {"domain": {"user_id": []}}
    #     # if self.team_id:
    #     #     return {"domain": {"user_id": [("id", "in", self.user_ids.ids)]}}
    #     else:
    #         return {"domain": {"user_id": []}}

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        # if vals.get("number", "/") == "/":
        #     vals["number"] = self._prepare_freight_booking_number(vals)
        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        # if "number" not in default:
        #     default["number"] = self._prepare_freight_booking_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for _ticket in self:
            now = fields.Datetime.now()
            # if vals.get("stage_id"):
            #     stage = self.env["freight.catalog.stage"].browse([vals["stage_id"]])
            #     vals["last_stage_update"] = now
            #     if stage.completed:
            #         vals["completed_date"] = now
            if vals.get("user_id"):
                vals["bill_date"] = now
        return super().write(vals)

    # def action_duplicate_freight_booking(self):
    #     for booking in self.browse(self.env.context["active_ids"]):
    #         booking.copy()

    # def _prepare_freight_booking_number(self, values):
    #     seq = self.env["ir.sequence"]
    #     if "company_id" in values:
    #         seq = seq.with_company(values["company_id"])
    #     return seq.next_by_code("freight.billing.sequence") or "/"

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        # freight_booking = self[0]
        # if "stage_id" in tracking and freight_booking.stage_id.mail_template_id:
        #     res["stage_id"] = (
        #         freight_booking.stage_id.mail_template_id,
        #         {
        #             "auto_delete_message": True,
        #             "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
        #                 "mail.mt_note"
        #             ),
        #             "email_layout_xmlid": "mail.mail_notification_light",
        #         },
        #     )
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "party_email": msg.get("from"),
            "party_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        freight_billing = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        party_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=freight_billing, force_create=False
            )
            if p
        ]
        freight_billing.message_subscribe(party_ids)

        return freight_billing

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        party_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(party_ids)
        return super().message_update(msg, update_vals=update_vals)

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for billing in self:
                if billing.party_id:
                    billing._message_add_suggested_recipient(
                        recipients, partner=billing.party_id, reason=_("Customer")
                    )
                elif billing.party_email:
                    billing._message_add_suggested_recipient(
                        recipients,
                        email=billing.party_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients
