# -*- coding: utf-8 -*-

import pytz
from datetime import datetime

from odoo import _, api, fields, models, tools
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.osv import expression
from odoo.tools import html_keep_url

from datetime import date, timedelta
from collections import defaultdict

class FreightBilling(models.Model):
    _name = "freight.billing"
    _description = "Freight Billing"
    _rec_name = "display_name"
    _order = "name desc"
    _mail_post_access = "read"
    _inherit = ["portal.mixin", "mail.thread.cc", "mail.activity.mixin"]

    def _compute_access_url(self):
        super(FreightBilling, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/notes/%s' % (order.id)

    def _get_portal_return_action(self):
        """ Return the action used to display bills when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('freight_mgmt.freight_billing_action')

    @api.model
    def _default_note(self):
        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        if use_invoice_terms and self.env.company.terms_type == "html":
            baseurl = html_keep_url(self._default_note_url() + '/terms')
            return _('Terms & Conditions: %s', baseurl)
        return use_invoice_terms and self.env.company.invoice_terms or ''

    # def _default_billing_number(self):
    #     seq = self.env["ir.sequence"]
    #     # if "company_id" in values:
    #     #     seq = seq.with_company(values["company_id"])
    #     return seq.next_by_code("freight.billing.sequence") or "Draft"

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    # ==== Business fields ====
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, tracking=True, default='draft', group_expand='_expand_states')

    # number = fields.Char(string="Bill number")
    name = fields.Char(string='Bill Number', default="#", readonly=True, store=True, index=True, required=True)
    display_name = fields.Char(string='Bill Number', compute="_compute_display_name")
    vessel_bol_number = fields.Char(string="B/L Number", tracking=True)
    description = fields.Char(translate=True, tracking=True)

    shipper_id = fields.Many2one(comodel_name="res.partner",
                                 domain=["|", ("category_id.name", "=", "Shipper"), ('category_id.name','=ilike', 'Người giao hàng')],
                                 string="Shipper", tracking=True)
    shipper_name = fields.Char()
    shipper_email = fields.Char(string="Shipper's Email")
    shipper_address = fields.Char(string="Shipper's Address", tracking=True)
    shipper_extra_info = fields.Char(string="Shipper's Information", tracking=True)

    consignee_id = fields.Many2one(comodel_name="res.partner",
                                   domain=["|", ("category_id.name", "=", "Consignee"), ('category_id.name','=ilike', 'Người nhận hàng')],
                                   string="Consignee", tracking=True)
    consignee_name = fields.Char()
    consignee_email = fields.Char(string="Consignee's Email")
    consignee_address = fields.Char(string="Consignee's Address", tracking=True)
    consignee_extra_info = fields.Char(string="Consignee's Information", tracking=True)

    party_id = fields.Many2one(comodel_name="res.partner", string="Party Notification", tracking=True)
    party_name = fields.Char()
    party_email = fields.Char(string="Party's Email")
    party_address = fields.Char(string="Party's Address", tracking=True)
    party_extra_info = fields.Char(string="Party's Information", tracking=True)

    contact_id = fields.Many2one(comodel_name="res.partner", string="Delivery Contact", tracking=True)
    contact_name = fields.Char()
    contact_email = fields.Char(string="Contact's Email")
    contact_address = fields.Char(string="Contact's Address", tracking=True)
    contact_extra_info = fields.Char(string="Contact's Information", tracking=True)

    note = fields.Html('Terms and conditions', default=_default_note, tracking=True)

    billing_type = fields.Selection([
        ('mbl', 'Master B/L'),
        ('hbl', 'House B/L'),
    ], string='B/L Type', default='mbl', required=True, tracking=True)

    order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order Reference",
        domain="['|', ('invoice_status','=','to invoice'), ('invoice_status','=','invoiced')]",
        tracking=True, index=True, readonly=True
    )
    partner_id = fields.Many2one(comodel_name="res.partner",
                                 string="Customer", readonly=True)

    booking_id = fields.Many2one(
        comodel_name="freight.booking", string="Booking",
        # domain="['&',('confirmed', '=', True), ('billing_id', '=', False)]",
        domain=lambda self: self._get_booking_id_domain(),
        tracking=True, index=True, required=True
    )
    vessel_booking_number = fields.Char(related="booking_id.vessel_booking_number",
                                        string="Booking Number", readonly=True, store=False)
    ''' TODO: FK port_loading_id in database is deprecated, now it uses related field. Consider to drop column in DB '''
    port_loading_id = fields.Many2one(related="booking_id.port_loading_id", string="Port of loading",
                                      readonly=False, store=False, tracking=True)
    port_discharge_id = fields.Many2one(related="booking_id.port_discharge_id", string="Port of discharge",
                                        readonly=False, store=False, tracking=True)
    port_stopover_id = fields.Many2one(related="booking_id.port_stopover_id", string="Stopover Port",
                                       readonly=False, store=False, tracking=True)
    vessel_id = fields.Many2one(related="booking_id.vessel_id", string="Ocean vessel",
                                readonly=True, store=False)
    vehicle_supplier_id = fields.Many2one(related="booking_id.vehicle_supplier_id", string="Vehicle Supplier",
                                          readonly=False, store=False, tracking=True)
    vehicle_number = fields.Char(related="booking_id.vehicle_number", readonly=False, store=True, tracking=True)
    shipment_type = fields.Selection(related="booking_id.shipment_type", string="Shipment Type", store=False,
                                     readonly=True, help='Type of Shipment')
    eta = fields.Datetime(related="booking_id.eta", string="ETA", store=False, readonly=True)
    port_loading_text = fields.Char(string="Port of loading text", tracking=True)
    port_discharge_text = fields.Char(string="Port of discharge text", tracking=True)
    port_stopover_text = fields.Char(string="Port of stopover text", tracking=True)
    pre_carriage = fields.Char(string="Pre-carriage by", tracking=True)
    delivery_place = fields.Char(string="Place of delivery", tracking=True)
    receipt_place = fields.Char(string="Place of receipt", tracking=True)
    container_number = fields.Char(string="Container No.", tracking=True)
    final_destination = fields.Char(string="Final destination", tracking=True)

    billing_line = fields.One2many('freight.billing.line', 'billing_id', string='Item Lines',
                                   states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                   auto_join=True, tracking=True)

    total_packages_word = fields.Char(string="Total Packs (in word)", tracking=True)
    freight_charge_rate = fields.Char(string="Charge types", tracking=True)
    rated_as = fields.Char(string="Rated as", tracking=True)
    payment_place = fields.Char(string="Place of payment", tracking=True)
    issue_type = fields.Char(string="Type of issue", tracking=True)
    movement_type = fields.Char(string="Type of movement", tracking=True)
    payable_at = fields.Char(string="Payable at", tracking=True)
    shipping_mark = fields.Char(string="Shipping mark", tracking=True)

    bill_date = fields.Datetime(string="Bill Date", default=fields.Datetime.now, tracking=True)
    due_date = fields.Datetime(string="Due Date", tracking=True)

    sale_order_count = fields.Integer("Sale Count", compute='_compute_sale_order_count')
    purchase_order_count = fields.Integer("Purchase Count", compute='_compute_purchase_order_count')
    debit_count = fields.Integer("Debit Count", compute='_compute_debit_count')
    credit_count = fields.Integer("Credit Count", compute='_compute_credit_count')
    show_create_credit_button = fields.Boolean("Check Credit Note Button", compute='_compute_credit_count')

    etd_formatted = fields.Char(compute="_compute_format_etd", string="ETD", readonly=True, store=False)
    do_number_ref = fields.Char(related="booking_id.number", string="DO No. Ref", store=False, readonly=True)
    do_number = fields.Char(compute="_compute_delivery_order_number", string="DO Number",
                            readonly=False, tracking=True, store=True)

    user_id = fields.Many2one(
        comodel_name="res.users", string="Assigned user", tracking=True, index=True
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    branch_id = fields.Many2one(related="booking_id.branch_id", string='Branch', store=True)

    debit_note_ids = fields.One2many('freight.debit.note', 'bill_id', string='Debit Note',
                                     copy=True, auto_join=True)
    credit_note_ids = fields.One2many('freight.credit.note', 'bill_id', string='Credit Note',
                                      copy=True, auto_join=True)

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    sequence = fields.Integer(default=16)

    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked")
        ],
    )
    active = fields.Boolean(default=True, tracking=True)

    def name_get(self):
        res = []
        for rec in self:
            # res.append((rec.id, rec.number + " - " + rec.name))
            if rec.env.context.get('display_by') == "vessel_bol_number":
                res.append((rec.id, rec.vessel_bol_number))
            elif rec.env.context.get('display_by') == "name_and_vessel_bol_number":
                name = '%s (%s)' % (rec.name, rec.vessel_bol_number)
                res.append((rec.id, name))
            else:
                res.append((rec.id, rec.name))
        return res

    @api.depends('name', 'vessel_bol_number')
    def _compute_display_name(self):
        for rec in self:
            display_by = rec.env.context.get('display_by')
            is_expenses = rec.env.context.get('search_default_my_expenses')
            if display_by == "vessel_bol_number":
                rec.display_name = rec.vessel_bol_number
            elif display_by == "name_and_vessel_bol_number" or is_expenses:
                rec.display_name = f"{rec.name} ({rec.vessel_bol_number})"
            else:
                rec.display_name = rec.name

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        # Custom search logic here
        if name:
            args = list(args or [])
            domain = ['|', ('name', operator, name), ('vessel_bol_number', operator, name)]
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
            # args += ['|', ('name', operator, name), ('vessel_bol_number', operator, name)]

        return super(FreightBilling, self)._name_search(name=name, args=args, operator=operator,
                                                        limit=limit, name_get_uid=name_get_uid)

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    def action_confirm(self):
        if not self.vessel_bol_number:
            raise UserError(_("A B/L Number is required in order to confirm a bill."))

        self.write({'state': 'posted'})

    # ---------------------------------------------------
    # Create Debit Note Action
    # ---------------------------------------------------

    def create_debit_note(self):
        # 1) Create debit notes.
        debit_vals_list = []
        for billing in self:
            debit_vals = self._prepare_debit_values(billing)

            debit_vals_list.append(debit_vals)

        if not debit_vals_list:
            raise self._nothing_to_debit_error()

        new_debits = self.env['freight.debit.note'].sudo().with_context().create(debit_vals_list)

        if new_debits:
            return self._open_view_debit_note(new_debits)

    def _open_view_debit_note(self, new_debits):
        debit_form = self.env.ref('freight_mgmt.freight_debit_note_view_form', False)

        if isinstance(new_debits.ids, list):
            new_debit_id = new_debits.ids[0]
        else:
            new_debit_id = new_debits.id

        if debit_form and new_debit_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'freight.debit.note',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'views': [(debit_form.id, 'form')],
                'view_id': debit_form.id,
                'res_id': new_debit_id,
            }

    def _prepare_debit_values(self, billing):
        debit_vals = {
            'bill_id': billing.id,
            # 'booking_id': billing.booking_id,
            # 'order_id': billing.order_id,
        }

        if billing.order_id and billing.order_id.partner_id:
            partner_id = billing.order_id.partner_id

            # invoice_partner_id = billing.order_id.partner_id.address_get(
            #     adr_pref=['invoice']).get('invoice', billing.order_id.partner_id)

            # if invoice_partner_id:
            partner_name = partner_id.commercial_company_name

            address = partner_id.contact_address
            if address and partner_name and partner_name in address:
                address = address.replace(partner_name, '')

            debit_vals['partner_name'] = partner_name
            debit_vals['partner_address'] = address

        debit_items = []
        if billing.order_id:
            debit_vals['exchange_rate'] = billing.order_id.exchange_rate

            for item in billing.order_id.order_line:
                vals = {
                    "external_id": item.id,
                    "sequence": item.sequence,
                    "name": item.name,
                    "quantity": item.product_uom_qty,
                    "uom": item.product_uom.display_name,
                    "unit_price": item.price_unit_input,
                    "currency_id": item.order_line_currency_id.id if item.order_line_currency_id else False,
                    "tax_id": item.tax_id,
                    "price_subtotal": item.price_subtotal_display,
                    "price_total": item.price_total_display,
                }
                if item.order_line_currency_id and item.order_line_currency_id.name == 'VND':
                    vals['price_tax'] = item.price_tax_vnd
                else:
                    vals['price_tax'] = item.price_tax

                debit_items.append((0, 0, vals))

        if debit_items:
            debit_vals['debit_items'] = debit_items

        return debit_vals

    def preview_debit_note(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    # ---------------------------------------------------
    # Create Credit Note Action
    # ---------------------------------------------------

    def create_credit_note(self):
        # 1) Create credit notes.
        credit_vals_list = []
        for billing in self:
            if billing.order_id:
                domain = [('state', 'in', ('purchase', 'done')), ("origin", "=", billing.order_id.name)]
                purchase_orders = self.env["purchase.order"].sudo().search(domain)
                if purchase_orders:
                    for order in purchase_orders:
                        if not order.credit_note_id:
                            credit_vals = self._prepare_credit_values(billing, order)
                            credit_vals_list.append(credit_vals)

        if not credit_vals_list:
            raise self._nothing_to_credit_error()

        new_credits = self.env['freight.credit.note'].sudo().with_context().create(credit_vals_list)

        if new_credits:
            return self.action_view_credit_note()

    @staticmethod
    def _prepare_credit_values(billing, purchase_order_id):
        credit_vals = {
            'bill_id': billing.id,
            'booking_id': billing.booking_id,
            'sale_order_id': billing.order_id,
        }

        if purchase_order_id:
            if purchase_order_id.state != 'purchase' and purchase_order_id.state != 'done':
                raise UserError(_(
                    "The Purchase Order must be confirmed in order to create a credit note.\n\n"
                ))

            credit_vals['purchase_order_id'] = purchase_order_id.id
            credit_vals['exchange_rate'] = purchase_order_id.exchange_rate

            if purchase_order_id.partner_id:
                partner_id = purchase_order_id.partner_id
                # credit_vals['partner_vat'] = partner_id.vat

                partner_name = partner_id.commercial_company_name

                address = partner_id.contact_address
                if address and partner_name and partner_name in address:
                    address = address.replace(partner_name, '')

                credit_vals['partner_name'] = partner_name
                credit_vals['partner_address'] = address

            credit_items = []
            for item in purchase_order_id.order_line:
                vals = {
                    # "credit_id": self.id,
                    "external_id": item.id,
                    "sequence": item.sequence,
                    "name": item.name,
                    "quantity": item.product_uom_qty,
                    "uom": item.product_uom.display_name,
                    "unit_price": item.price_unit,
                    "currency_id": item.order_line_currency_id.id if item.order_line_currency_id else False,
                    "tax_id": item.taxes_id,
                    "price_subtotal": item.price_subtotal_display,
                    "price_total": item.price_total_display,
                }
                if item.order_line_currency_id and item.order_line_currency_id.name == 'VND':
                    vals['price_tax'] = item.price_tax_vnd
                else:
                    vals['price_tax'] = item.price_tax

                credit_items.append((0, 0, vals))

            if credit_items:
                credit_vals['credit_items'] = credit_items

        return credit_vals

    @api.model
    def _nothing_to_debit_error(self):
        return UserError(_(
            "No available sale order selected to create debit note! Please contact administrator for details.\n\n"
        ))

    @api.model
    def _nothing_to_credit_error(self):
        return UserError(_(
            "No available purchase order selected to create credit note! Please contact administrator for details.\n\n"
        ))

    @api.model
    def _get_booking_id_domain(self):
        if self.env.context.get("shipment_type_suffix") == 'imp':
            res = [('shipment_type', 'in', ('fcl-imp', 'lcl-imp', 'air-imp')),
                   ('confirmed', '=', True), ('billing_id', '=', False)]
        else:
            res = [('shipment_type', 'not in', ('fcl-imp', 'lcl-imp', 'air-imp')),
                   ('confirmed', '=', True), ('billing_id', '=', False)]
        return res

    def action_view_sale_order(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "domain": [['id', 'in', self.order_id.ids]],
            "name": "Sale Order",
            'view_mode': 'tree,form',
        }
        if len(self.order_id) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = self.order_id.id
        return result

    def action_view_purchase_order(self):
        self.ensure_one()
        purchase_orders = self.env['purchase.order'].search([
            ("origin", "=", self.order_id.name)
        ])
        if not purchase_orders:
            return

        purchase_order_view_form = self.env.ref('freight_mgmt.freight_purchase_order_view_form_from_billing_inherited', False)

        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window'
        }
        if len(purchase_orders) == 1:
            action.update({
                'res_id': purchase_orders.id,
                'view_type': 'tree',
                'view_mode': 'form',
                'views': [(purchase_order_view_form.id, 'form')],
                'view_id': purchase_order_view_form.id
            })
        else:
            action.update({
                'name': _("Purchase Order generated from %s", self.order_id.name),
                'domain': [('id', 'in', purchase_orders.ids)],
                'view_mode': 'tree,form'
            })
        return action

    def action_view_debit_note(self):
        self.ensure_one()
        debit_notes = self.env['freight.debit.note'].search([
            ('bill_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "freight.debit.note",
            "domain": [['id', 'in', debit_notes.ids]],
            "name": "Debit Notes",
            'view_mode': 'tree,form',
        }
        if len(debit_notes) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = debit_notes.id
        return result

    def action_view_credit_note(self):
        self.ensure_one()
        credit_notes = self.env['freight.credit.note'].search([
            ('bill_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "freight.credit.note",
            "domain": [['id', 'in', credit_notes.ids]],
            "name": "Credit Notes",
            'view_mode': 'tree,form',
        }
        if len(credit_notes) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = credit_notes.id
        return result

    @api.model
    def automate_action_update_bl_number_invoice(self, record):
        """
        An automated action to update BL number in invoice when this field has just been updated.
        This automated action is necessary because it doesn't automate update the field in invoice accordingly.

        :param record: a billing record just updated (no need to trigger for creation)
        """
        try:
            if not record or not record.vessel_bol_number:
                return False

            related_so_name = record.order_id.name if record.order_id else ''
            related_po_name = ''
            if related_so_name:
                related_purchase_order = self.env['purchase.order'].sudo().search([
                    ('origin', '=', related_so_name)
                ], limit=1)
                if related_purchase_order:
                    related_po_name = related_purchase_order.name

            if related_so_name or related_po_name:
                array_origins = []
                if related_so_name:
                    array_origins.append(related_so_name)
                if related_po_name:
                    array_origins.append(related_po_name)

                related_invoices = self.env['account.move'].sudo().search([('invoice_origin', 'in', array_origins)])
                if related_invoices:
                    related_invoices.write({'vessel_bol_number': record.vessel_bol_number})

            print("automate_action_update_bl_number_invoice - executed successful.")
        except Exception as e:
            print("automate_action_update_bl_number_invoice - Exception: " + str(e))

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

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s' % (self.display_name)

    def _compute_sale_order_count(self):
        for bill in self:
            bill.sale_order_count = len(bill.order_id)

    def _compute_purchase_order_count(self):
        for bill in self:
            so_name = bill.order_id.name if bill.order_id else False
            if so_name:
                bill.purchase_order_count = self.env['purchase.order'].sudo().search_count([
                    ('origin', '=', so_name)
                ])
            else:
                bill.purchase_order_count = 0

    def _compute_debit_count(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for bill in self:
            bill.debit_count = self.env['freight.debit.note'].search_count([
                ('bill_id', '=', bill.id)
            ])

    def _compute_credit_count(self):
        for bill in self:
            bill.credit_count = 0
            bill.show_create_credit_button = True
            if bill.credit_note_ids:
                bill.credit_count = len(bill.credit_note_ids)

                if bill.order_id:
                    domain = [('state', 'in', ('purchase', 'done')), ("origin", "=", bill.order_id.name)]
                    purchase_orders_count = self.env["purchase.order"].sudo().search_count(domain)
                    bill.show_create_credit_button = bill.credit_count < purchase_orders_count

    @api.depends('do_number_ref')
    def _compute_delivery_order_number(self):
        for rec in self:
            rec.do_number = rec.do_number_ref + "-DO" if rec.do_number_ref else "#-DO"

    @api.depends('booking_id.etd_revised')
    def _compute_format_etd(self):
        for rec in self:
            rec.etd_formatted = ''
            if rec.booking_id.etd_revised:
                etd_local = self._convert_utc_to_local(rec.booking_id.etd_revised)
                if etd_local:
                    rec.etd_formatted = etd_local.strftime('%d-%B-%Y')

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

    # @api.onchange("order_id")
    # def _onchange_order_id(self):
    #     if self.order_id:
    #         self.user_id = self.order_id.user_id
    #         self.partner_id = self.order_id.partner_id

    # @api.onchange("booking_id")
    # def _onchange_booking_id(self):
    #     if self.booking_id:
    #         self.port_loading_id = self.booking_id.port_loading_id
    #         self.port_discharge_id = self.booking_id.port_discharge_id
    #         self.vessel_id = self.booking_id.vessel_id

    @api.onchange("port_loading_id")
    def _onchange_port_loading_id(self):
        if self.port_loading_id:
            if self.port_loading_id.printing_name:
                self.port_loading_text = self.port_loading_id.printing_name
            else:
                self.port_loading_text = self.port_loading_id.name
                if self.port_loading_id.country_id:
                    self.port_loading_text += ', ' + self.port_loading_id.country_id.name

            self.receipt_place = self.port_loading_text

    @api.onchange("port_discharge_id")
    def _onchange_port_discharge_id(self):
        if self.port_discharge_id:
            if self.port_discharge_id.printing_name:
                self.port_discharge_text = self.port_discharge_id.printing_name
            else:
                self.port_discharge_text = self.port_discharge_id.name
                if self.port_discharge_id.country_id:
                    self.port_discharge_text += ', ' + self.port_discharge_id.country_id.name

    @api.onchange("port_stopover_id")
    def _onchange_port_stopover_id(self):
        if self.port_stopover_id:
            if self.port_stopover_id.printing_name:
                self.port_stopover_text = self.port_stopover_id.printing_name
            else:
                self.port_stopover_text = self.port_stopover_id.name
                if self.port_stopover_id.country_id:
                    self.port_stopover_text += ', ' + self.port_stopover_id.country_id.name

    @api.onchange("shipper_id")
    def _onchange_shipper_id(self):
        if self.shipper_id:
            self.shipper_name = self.shipper_id.name
            self.shipper_email = self.shipper_id.email
            self.shipper_address = self.shipper_id.contact_address
            if self.shipper_address:
                self.shipper_address = self.shipper_address.replace(self.shipper_name, '')

            self.shipper_extra_info = ''
            if self.shipper_id.phone:
                self.shipper_extra_info += 'TEL: ' + self.shipper_id.phone
            elif self.shipper_id.mobile:
                self.shipper_extra_info += 'TEL: ' + self.shipper_id.mobile
            if self.shipper_email:
                self.shipper_extra_info += ' - MAIL: ' + self.shipper_email
            if self.shipper_id.vat:
                self.shipper_extra_info += ' - VAT: ' + self.shipper_id.vat

    @api.onchange("consignee_id")
    def _onchange_consignee_id(self):
        if self.consignee_id:
            self.consignee_name = self.consignee_id.name
            self.consignee_email = self.consignee_id.email
            self.consignee_address = self.consignee_id.contact_address
            if self.consignee_address:
                self.consignee_address = self.consignee_address.replace(self.consignee_name, '')

            self.consignee_extra_info = ''
            if self.consignee_id.phone:
                self.consignee_extra_info += 'TEL: ' + self.consignee_id.phone
            elif self.consignee_id.mobile:
                self.consignee_extra_info += 'TEL: ' + self.consignee_id.mobile
            if self.consignee_email:
                self.consignee_extra_info += ' - MAIL: ' + self.consignee_email
            if self.consignee_id.vat:
                self.consignee_extra_info += ' - VAT: ' + self.consignee_id.vat

    @api.onchange("party_id")
    def _onchange_party_id(self):
        if self.party_id:
            self.party_name = self.party_id.name
            self.party_email = self.party_id.email
            self.party_address = self.party_id.contact_address
            if self.party_address:
                self.party_address = self.party_address.replace(self.party_name, '')

            self.party_extra_info = ''
            if self.party_id.phone:
                self.party_extra_info += 'TEL: ' + self.party_id.phone
            elif self.party_id.mobile:
                self.party_extra_info += 'TEL: ' + self.party_id.mobile
            if self.party_email:
                self.party_extra_info += ' - MAIL: ' + self.party_email
            if self.party_id.vat:
                self.party_extra_info += ' - VAT: ' + self.party_id.vat

    @api.onchange("contact_id")
    def _onchange_contact_id(self):
        if self.contact_id:
            self.contact_name = self.contact_id.name
            self.contact_email = self.contact_id.email
            self.contact_address = self.contact_id.contact_address
            if self.contact_address:
                self.contact_address = self.contact_address.replace(self.contact_name, '')

            self.contact_extra_info = ''
            if self.contact_id.phone:
                self.contact_extra_info += 'TEL: ' + self.contact_id.phone
            elif self.contact_id.mobile:
                self.contact_extra_info += 'TEL: ' + self.contact_id.mobile
            if self.contact_email:
                self.contact_extra_info += ' - MAIL: ' + self.contact_email
            if self.contact_id.vat:
                self.contact_extra_info += ' - VAT: ' + self.contact_id.vat

    # @api.onchange("user_id")
    # def _onchange_dominion_user_id(self):
    #     if self.user_id: # and self.user_ids:
    #         self.update({"user_id": False})
    #         return {"domain": {"user_id": []}}
    #     # if self.team_id:
    #     #     return {"domain": {"user_id": [("id", "in", self.user_ids.ids)]}}
    #     else:
    #         return {"domain": {"user_id": []}}

    def update_total_pkgs_dict(self, dict_to_update, key, value_number):
        if not value_number:
            return dict_to_update

        if not key:
            key = ' '

        if key in dict_to_update:
            dict_to_update[key] += value_number
        else:
            dict_to_update[key] = value_number

        return dict_to_update

    def generate_no_of_pkgs(self, dict_to_concat):
        res = ''
        if self.booking_id and self.booking_id.volumes_display:
            res += self.booking_id.volumes_display.replace(',', '<br/>') + '<br/><br/>'
        if dict_to_concat:
            res += ''.join('{:,.2f}'.format(dict_to_concat[key]) + ' ' + key + '<br/>' for key in dict_to_concat.keys())

        return res

    @staticmethod
    def update_delivery_order_total_pkgs_dict(dict_to_update, key, value_number):
        if not value_number:
            return dict_to_update

        if not key:
            key = ' '

        if key in dict_to_update:
            dict_to_update[key] += value_number
        else:
            dict_to_update[key] = value_number

        return dict_to_update

    @staticmethod
    def generate_delivery_order_no_of_pkgs(dict_to_concat):
        res = ''
        if dict_to_concat:
            for key in dict_to_concat.keys():
                # Remove trailing .0 or . at the end
                quantity_formatted = '{:,.2f}'.format(dict_to_concat[key]).rstrip('0').rstrip('.')
                res += ''.join(quantity_formatted + ' ' + key + '<br/>')
        return res

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("name", "#") == "#":
            vals["name"] = self._prepare_freight_billing_number(vals)
        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "name" not in default:
            default["nam"] = self._prepare_freight_billing_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for item in self:
            now = fields.Datetime.now()
            if vals.get("state") in ['posted', 'completed'] and not item.vessel_bol_number:
                raise UserError(_("A B/L Number is required in order to update a bill."))

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

    def _prepare_freight_billing_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("freight.billing.sequence") or "#"

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
