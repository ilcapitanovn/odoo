# -*- coding: utf-8 -*-

import pytz
from datetime import datetime

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError
from odoo.tools import html_keep_url, float_round

PAYMENT_STATE_SELECTION = [
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
]


class FreightDebitNote(models.Model):
    _name = "freight.debit.note"
    _description = "Freight Debit Note"
    _rec_name = "id"
    _order = "id desc"
    _mail_post_access = "read"
    _inherit = ["portal.mixin", "mail.thread.cc", "mail.activity.mixin"]

    def _compute_access_url(self):
        super(FreightDebitNote, self)._compute_access_url()
        for debit in self:
            debit.access_url = '/my/notes/%s' % (debit.id)

    def _get_portal_return_action(self):
        """ Return the action used to display bills when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('freight_mgmt.freight_debit_note_action')

    def _get_default_exchange_rate(self):
        #usd = self.env['res.currency'].search([('name', '=', 'USD')])
        #vnd = self.env['res.currency'].search([('name', '=', 'VND')])
        vnd = self.env['res.currency'].search([('name', '=', 'VND')], limit=1)
        #company = self.order_id.company_id
        #amount_vnd = usd._convert(self.order_id.amount_total, vnd, company, self.debit_date)
        # rate = 0
        # if vnd:
        #     rate = vnd.rate
        vnd_rate = vnd.rate if vnd else 0
        return float_round(vnd_rate, precision_digits=0)

    @api.model
    def _default_note(self):
        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        if use_invoice_terms and self.env.company.terms_type == "html":
            baseurl = html_keep_url(self._default_note_url() + '/terms')
            return _('Terms & Conditions: %s', baseurl)
        return use_invoice_terms and self.env.company.invoice_terms or ''

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    # ==== Business fields ====
    number = fields.Char(string='Debit Number', default="#", readonly=True, store=True, index=True, required=True)
    bill_id = fields.Many2one(
        comodel_name="freight.billing", string="Bill Reference",
        domain="['&',('state', 'in', ['posted', 'completed']), ('debit_note_ids', '=', False)]",
        tracking=True, index=True, required=True
    )

    debit_date = fields.Datetime(string="Debit date", default=fields.Datetime.now)
    exchange_rate = fields.Float(string='Exchange rate', default=_get_default_exchange_rate, readonly=False,
                        help='The rate of the currency to the currency of rate 1.', store=True)

    bill_no = fields.Char(related="bill_id.vessel_bol_number",
                          string="BL Number", readonly=True, store=False)
    booking_id = fields.Many2one(related="bill_id.booking_id", string="Booking", readonly=True)
    order_id = fields.Many2one(related="bill_id.order_id", string="Sale Order Reference", readonly=True)
    partner_id = fields.Many2one(related="order_id.partner_id", string="Partner", readonly=True)
    user_id = fields.Many2one(related="order_id.user_id", string="S.I.C")
    invoice_count = fields.Integer(related="order_id.invoice_count", string='Invoice Count', copy=False)
    invoice_status = fields.Selection(related="order_id.invoice_status", string="Invoice Status", store=True)
    sale_state = fields.Selection(related="order_id.state", string="Sale Order State", store=True)

    pol = fields.Char(related="bill_id.port_loading_id.name", string="POL", readonly=True, store=False)
    pod = fields.Char(related="bill_id.port_discharge_id.name", string="POD", readonly=True, store=False)
    etd = fields.Datetime(related="booking_id.etd_revised", string="ETD", readonly=True, store=False)
    etd_formatted = fields.Char(compute="_compute_format_etd", string="ETD", readonly=True, store=False)
    volume = fields.Char(compute="_compute_booking_volumes", string="VOLUME", readonly=True, store=False)

    customer_id = fields.Many2one(related="partner_id", string="Customer", readonly=False, store=False)
    invoice_partner_id = fields.Many2one('res.partner', compute='_get_invoice_partner_id',
                                         string='Invoice Address')
    partner_vat = fields.Char(related="partner_id.vat", store=True, string="VAT", readonly=False)
    partner_name = fields.Char(string="Company Name", compute="_get_partner_name",
                               store=True, readonly=False)
    partner_address = fields.Char(string="Address", compute="_parse_address_from_contact_address",
                                  store=True, readonly=False)

    debit_items = fields.One2many('freight.debit.note.item', 'debit_id', string='Debit Note Items',
                                  store=True, copy=True, auto_join=True)
    # amount_total = fields.Monetary(related="order_id.amount_total", string="Total", readonly=True, store=True)
    amount_total = fields.Monetary(compute="_compute_subtotal", string="Total", readonly=True, store=True)
    amount_subtotal_vnd = fields.Monetary(compute="_compute_subtotal", string="Total", readonly=True, store=True)
    amount_total_vnd = fields.Monetary(compute="_compute_amount_total_vnd", string="Total", readonly=True)

    # user_id = fields.Many2one(
    #     comodel_name="res.users", string="Assigned user", tracking=True, index=True
    # )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    bank_ids = fields.One2many(related="company_id.bank_ids")
    company_bank_id = fields.Many2one('res.partner.bank', string="Company Bank Account",
                                      readonly=True, store=True,
                                      compute='_compute_company_bank_id',
                                      domain="[('id', 'in', bank_ids)]",
                                      check_company=True)
    bank_name = fields.Char(related="company_bank_id.bank_name", string="Bank Name")
    bank_acc_no = fields.Char(related="company_bank_id.acc_number", string="Account Number")
    bank_acc_name = fields.Char(related="company_bank_id.acc_holder_name", string="Account Holder Name")
    swift_code = fields.Char(related="company_bank_id.bank_bic", string="Swift Code")

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    sequence = fields.Integer(default=16)

    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status",
                                     readonly=True, copy=False, tracking=True, compute='_compute_payment_state')
    payment_term = fields.Char(compute="_compute_payment_term", string="Payment Term", readonly=True, store=False)

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('completed', 'Completed'),
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
            res.append((rec.id, rec.number))
        return res

    def preview_debit_note(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def update_exchange_rate(self):
        self.ensure_one()
        self.exchange_rate = self._get_default_exchange_rate()

    def action_create_invoice(self):
        if not self.order_id and self.order_id.invoice_status != 'to invoice':
            raise UserError(_("The selected Bill and its Sale Order is invalid to invoice."))
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        action['context'] = {
            'active_id': self.order_id.ids[0] if len(self.order_id.ids) == 1 else False,
            'active_ids': self.order_id.ids
        }
        return action

    def action_view_invoice(self):
        if not self.order_id:
            raise UserError(_("The selected Debit Note and its Invoices is invalid to view."))
        action = self.order_id.action_view_invoice()
        return action

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in type(self).state.selection]

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s' % (self.display_name)

    def _get_invoice_partner_id(self):
        for rec in self:
            rec.invoice_partner_id = rec.partner_id.address_get(
                adr_pref=['invoice']).get('invoice', rec.partner_id.id)

    @api.depends('bank_ids')
    def _compute_company_bank_id(self):
        ''' The default company_bank_id will be the first available on the company. '''
        for debit in self:
            if debit.bank_ids:
                debit.company_bank_id = debit.bank_ids[:1]._origin

    @api.depends('etd')
    def _compute_format_etd(self):
        for rec in self:
            etd_local = self._convert_utc_to_local(rec.etd)
            if etd_local:
                rec.etd_formatted = etd_local.strftime('%d-%B-%Y')
            else:
                rec.etd_formatted = ''

    def _convert_utc_to_local(self, utc_date):
        result = utc_date
        if result:
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                utc_date_str = utc_date.strftime(fmt)

                ########################################################
                # OPTION 1
                ########################################################
                # now_utc = datetime.now(pytz.timezone('UTC'))
                # tz = pytz.timezone(self.env.user.tz)      # Consider get tz correct
                # now_tz = now_utc.astimezone(tz) or pytz.utc
                # utc_offset_timedelta = datetime.strptime(now_tz.strftime(fmt), fmt) - datetime.strptime(now_utc.strftime(fmt), fmt)
                # # local_date = datetime.strptime(utc_date_str, fmt)
                # result = utc_date + utc_offset_timedelta

                ########################################################
                # OPTION 2
                ########################################################
                timezone = 'UTC'
                if self.env.user.tz:
                    timezone = self.env.user.tz
                elif self.user_id and self.user_id.partner_id.tz:
                    timezone = self.user_id.partner_id.tz
                tz = pytz.timezone(timezone)
                result = pytz.utc.localize(datetime.strptime(utc_date_str, fmt)).astimezone(tz)
            except:
                print("ERROR in _convert_utc_to_local")

            return result

    @api.depends('booking_id')
    def _compute_booking_volumes(self):
        for rec in self:
            if rec.booking_id and rec.booking_id.booking_volumes:
                for item in rec.booking_id.booking_volumes:
                    if item.container_id:
                        if rec.volume:
                            rec.volume += ', %sx%s' % (item.quantity, item.container_id.code)
                        else:
                            rec.volume = '%sx%s' % (item.quantity, item.container_id.code)
            else:
                rec.volume = ''

    @api.depends('debit_items.price_total')
    def _compute_subtotal(self):
        """
        Compute the total amounts of the SO.
        """
        for debit in self:
            # amount_untaxed = amount_tax = 0.0
            amount_subtotal_usd = amount_subtotal_vnd = 0.0
            for item in debit.debit_items:
                # amount_untaxed += item.price_subtotal
                # amount_tax += item.price_tax
                if item.currency_id and item.currency_id.name == 'USD':
                    amount_subtotal_usd += item.price_total
                elif item.currency_id and item.currency_id.name == 'VND':
                    amount_subtotal_vnd += item.price_total
            debit.update({
                'amount_total': amount_subtotal_usd,
                'amount_subtotal_vnd': amount_subtotal_vnd,
            })

    @api.depends('amount_total', 'exchange_rate')
    def _compute_amount_total_vnd(self):
        for rec in self:
            rec.amount_total_vnd = float_round(rec.amount_total * rec.exchange_rate, precision_digits=0)
            if rec.amount_subtotal_vnd > 0:
                rec.amount_total_vnd += rec.amount_subtotal_vnd

    def _compute_payment_state(self):
        for rec in self:
            if rec.order_id and rec.order_id.invoice_ids:
                for invoice in rec.order_id.invoice_ids:
                    rec.payment_state = invoice.payment_state
            else:
                rec.payment_state = 'not_paid'

    @api.depends('partner_id')
    def _compute_payment_term(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.property_payment_term_id:
                rec.payment_term = rec.partner_id.property_payment_term_id.display_name
            else:
                rec.payment_term = ''

    def _get_partner_name(self):
        if self.invoice_partner_id:
            return self.invoice_partner_id.commercial_company_name
        return ""

    def _parse_address_from_contact_address(self):
        result = ''
        if self.invoice_partner_id:
            result = self.invoice_partner_id.contact_address
            if result and self.partner_name and self.partner_name in result:
                result = result.replace(self.partner_name, '')

        return result

    @api.onchange("bill_id", "customer_id")
    def _onchange_partner_id(self):
        if self.customer_id:
            self.invoice_partner_id = self.customer_id.address_get(
                adr_pref=['invoice']).get('invoice', self.customer_id.id)

            if self.invoice_partner_id:
                self.partner_name = self._get_partner_name()
                self.partner_address = self._parse_address_from_contact_address()
        else:
            self.partner_name = ""
            self.partner_address = ""

    @api.onchange("order_id")
    def _onchange_order_id(self):
        items = []
        if self.order_id and self.order_id.order_line:
            for item in self.order_id.order_line:
                vals = {
                    "debit_id": self.id,
                    "external_id": item.id,
                    "state": item.state,
                    "name": item.name,
                    "sequence": item.sequence,
                    "quantity": item.product_uom_qty,
                    "uom": item.product_uom.display_name,
                    "unit_price": item.price_unit,
                    "currency_id": item.currency_id.id if item.currency_id else False,
                    "tax_id": item.tax_id,
                    "price_subtotal": item.price_subtotal,
                    "price_tax": item.price_tax,
                    "price_total": item.price_total,
                }
                #self.fill_readonly_data_to_debit_item(vals, item)
                items.append((0, 0, vals))

        if items:
            self.debit_items = [(5, 0, 0)]
            self.debit_items = items
        else:
            self.debit_items = items.append((0, 0, {}))

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("number", "#") == "#":
            vals["number"] = self._prepare_freight_debit_note_number(vals)

        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_freight_debit_note_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        # for _ticket in self:
        #     now = fields.Datetime.now()
        #     # if vals.get("stage_id"):
        #     #     stage = self.env["freight.catalog.stage"].browse([vals["stage_id"]])
        #     #     vals["last_stage_update"] = now
        #     #     if stage.completed:
        #     #         vals["completed_date"] = now
        #     if not vals.get("debit_date"):
        #         vals["debit_date"] = now
        return super().write(vals)

    # def action_duplicate_freight_booking(self):
    #     for booking in self.browse(self.env.context["active_ids"]):
    #         booking.copy()

    def _prepare_freight_debit_note_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("freight.debit.note.sequence") or "#"

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
            "user_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        freight_debit_note = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        party_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=freight_debit_note, force_create=False
            )
            if p
        ]
        freight_debit_note.message_subscribe(party_ids)

        return freight_debit_note

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
            for debit in self:
                if debit.partner_id:
                    debit._message_add_suggested_recipient(
                        recipients, partner=debit.partner_id, reason=_("Customer")
                    )
                # elif debit.party_email:
                #     debit._message_add_suggested_recipient(
                #         recipients,
                #         email=debit.party_email,
                #         reason=_("Customer Email"),
                #     )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients
