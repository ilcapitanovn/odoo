# -*- coding: utf-8 -*-

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


class FreightCreditNote(models.Model):
    _name = "freight.credit.note"
    _description = "Freight Credit Note"
    _rec_name = "id"
    _order = "id desc"
    _mail_post_access = "read"
    _inherit = ["portal.mixin", "mail.thread.cc", "mail.activity.mixin"]

    def _compute_access_url(self):
        super(FreightCreditNote, self)._compute_access_url()
        for credit in self:
            credit.access_url = '/my/notes/%s' % (credit.id)

    def _get_portal_return_action(self):
        """ Return the action used to display bills when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('freight_mgmt.freight_credit_note_action')

    def _get_default_exchange_rate(self):
        vnd = self.env['res.currency'].search([('name', '=', 'VND')], limit=1)
        vnd_rate = vnd.rate if vnd else 0
        return float_round(vnd_rate, precision_digits=0)

    def _get_purchase_order_domain(self):
        domain = [('id', '=', -1)]
        filtered_order_id = self.sale_order_id._get_purchase_orders()
        if filtered_order_id:
            domain = [('id', 'in', filtered_order_id.ids)]
        return domain

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    # ==== Business fields ====
    number = fields.Char(string='Credit Number', default="#", readonly=True, store=True, index=True, required=True)
    bill_id = fields.Many2one(
        comodel_name="freight.billing", string="Bill Reference",
        domain="['&',('state', '=', 'posted'), ('credit_note_ids', '=', False)]",
        tracking=True, index=True, required=True
    )

    credit_date = fields.Datetime(string="Credit date", readonly=True, default=fields.Datetime.now)
    exchange_rate = fields.Float(string='Exchange rate', default=_get_default_exchange_rate, readonly=False,
                        help='The rate of the currency to the currency of rate 1.', store=True)

    bill_no = fields.Char(related="bill_id.vessel_bol_number",
                          string="BL Number", readonly=True, store=False)
    booking_id = fields.Many2one(related="bill_id.booking_id", string="Booking", readonly=True)
    sale_order_id = fields.Many2one(related="bill_id.order_id", string="Sale Order Reference", readonly=True)
    origin_name = fields.Char(related="sale_order_id.name", string="Source Document", readonly=True, store=False)
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Orders",
                                        domain="[('origin', '=', origin_name)]")
    partner_id = fields.Many2one(related="purchase_order_id.partner_id", string="Partner", readonly=True)
    user_id = fields.Many2one(related="purchase_order_id.user_id", string="S.I.C")
    invoice_count = fields.Integer(related="purchase_order_id.invoice_count", string='Bill Count', copy=False)
    invoice_ids = fields.Many2many(related="purchase_order_id.invoice_ids", string='Bills', copy=False)
    invoice_status = fields.Selection(related="purchase_order_id.invoice_status", string="Invoice Status", store=True)
    sale_state = fields.Selection(related="purchase_order_id.state", string="Purchase Order State", store=True)

    is_purchase_order_empty = fields.Boolean(compute='_compute_is_purchase_order_empty', store=False)

    pol = fields.Char(related="bill_id.port_loading_id.name", string="POL", readonly=True, store=False)
    pod = fields.Char(related="bill_id.port_discharge_id.name", string="POD", readonly=True, store=False)
    etd = fields.Datetime(related="booking_id.etd_revised", string="ETD", readonly=True, store=False)
    etd_formatted = fields.Char(compute="_compute_format_etd", string="ETD", readonly=True, store=False)
    volume = fields.Char(compute="_compute_booking_volumes", string="VOLUME", readonly=True, store=False)

    supplier_id = fields.Many2one(related="partner_id", string="Vendor", readonly=False, store=False)
    invoice_partner_id = fields.Many2one('res.partner', compute='_get_invoice_partner_id',
                                         string='Invoice Address')
    partner_vat = fields.Char(related="partner_id.vat", store=True, string="VAT", readonly=False)
    partner_name = fields.Char(string="Vendor Name", compute="_get_partner_name",
                               store=True, readonly=False)
    partner_address = fields.Char(string="Vendor Address", compute="_parse_address_from_contact_address",
                                  store=True, readonly=False)

    credit_items = fields.One2many('freight.credit.note.item', 'credit_id', string='Credit Note Items',
                                  store=True, copy=True, auto_join=True)
    # amount_total = fields.Monetary(related="purchase_order_id.amount_total", string="Total", readonly=True, store=True)
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
            res.append((rec.id, rec.number))
        return res

    def preview_credit_note(self):
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
        if self.purchase_order_id:
            action = self.purchase_order_id.action_create_invoice()
            return action

    def action_view_invoice(self, invoices=False):
        if self.purchase_order_id:
            action = self.purchase_order_id.action_view_invoice(invoices)
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

    @api.depends('purchase_order_id')
    def _compute_is_purchase_order_empty(self):
        if self.purchase_order_id:
            self.is_purchase_order_empty = False
        else:
            self.is_purchase_order_empty = True
        print("finish - remove after debug")

    @api.depends('bank_ids')
    def _compute_company_bank_id(self):
        ''' The default company_bank_id will be the first available on the company. '''
        for credit in self:
            if credit.bank_ids:
                credit.company_bank_id = credit.bank_ids[:1]._origin

    @api.depends('etd')
    def _compute_format_etd(self):
        for rec in self:
            if rec.etd:
                rec.etd_formatted = rec.etd.strftime('%d-%B-%Y')
            else:
                rec.etd_formatted = ''

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

    @api.depends('credit_items.price_total')
    def _compute_subtotal(self):
        """
        Compute the total amounts of the SO.
        """
        for credit in self:
            amount_subtotal_usd = amount_subtotal_vnd = 0.0
            for item in credit.credit_items:
                if item.currency_id and item.currency_id.name == 'USD':
                    amount_subtotal_usd += item.price_total
                elif item.currency_id and item.currency_id.name == 'VND':
                    amount_subtotal_vnd += item.price_total
            credit.update({
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
            if rec.purchase_order_id and rec.purchase_order_id.invoice_ids:
                for invoice in rec.purchase_order_id.invoice_ids:
                    rec.payment_state = invoice.payment_state
            else:
                rec.payment_state = 'not_paid'

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

    @api.depends('sale_order_id.order_line.purchase_line_ids.order_id')
    @api.onchange("bill_id")
    def _onchange_bill_id(self):
        filtered_order_id = self.sale_order_id._get_purchase_orders()

        if filtered_order_id:
            self.is_purchase_order_empty = False
            # res = {}
            # res['domain'] = {'purchase_order_id': [('id', 'in', filtered_order_id.ids)]}
            # return res
            # self.update({'purchase_order_id': [6, 0, filtered_order_id]})
        else:
            self.is_purchase_order_empty = True
            self.update({'purchase_order_id': [(5, 0, 0)]})

    @api.onchange("supplier_id")
    def _onchange_partner_id(self):
        if self.supplier_id:
            self.invoice_partner_id = self.supplier_id.address_get(
                adr_pref=['invoice']).get('invoice', self.supplier_id.id)

            if self.invoice_partner_id:
                self.partner_name = self._get_partner_name()
                self.partner_address = self._parse_address_from_contact_address()
        else:
            self.partner_name = ""
            self.partner_address = ""

    @api.onchange("purchase_order_id")
    def _onchange_purchase_order_id(self):
        items = []
        if self.purchase_order_id and self.purchase_order_id.order_line:
            for item in self.purchase_order_id.order_line:
                vals = {
                    "credit_id": self.id,
                    "external_id": item.id,
                    "state": item.state,
                    "name": item.name,
                    "sequence": item.sequence,
                    "quantity": item.product_uom_qty,
                    "uom": item.product_uom.display_name,
                    "unit_price": item.price_unit,
                    "currency_id": item.currency_id.id if item.currency_id else False,
                    "tax_id": item.taxes_id,
                    "price_subtotal": item.price_subtotal,
                    "price_tax": item.price_tax,
                    "price_total": item.price_total,
                }
                items.append((0, 0, vals))

        if items:
            self.credit_items = [(5, 0, 0)]
            self.credit_items = items
        else:
            self.credit_items = items.append((0, 0, {}))

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("number", "#") == "#":
            vals["number"] = self._prepare_freight_credit_note_number(vals)

        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_freight_credit_note_number(default)
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
            if not vals.get("credit_date"):
                vals["credit_date"] = now
        return super().write(vals)

    def _prepare_freight_credit_note_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("freight.credit.note.sequence") or "#"

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
        freight_credit_note = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        party_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=freight_credit_note, force_create=False
            )
            if p
        ]
        freight_credit_note.message_subscribe(party_ids)

        return freight_credit_note

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
            for credit in self:
                if credit.partner_id:
                    credit._message_add_suggested_recipient(
                        recipients, partner=credit.partner_id, reason=_("Customer")
                    )
                # elif credit.party_email:
                #     credit._message_add_suggested_recipient(
                #         recipients,
                #         email=credit.party_email,
                #         reason=_("Customer Email"),
                #     )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients
