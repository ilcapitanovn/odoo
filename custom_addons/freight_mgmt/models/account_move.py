# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
from datetime import timedelta

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # This field will also be used in inheritance models like account.payment
    exchange_rate = fields.Float(string='Exchange rate', compute="_compute_exchange_rate",
                                 tracking=True, store=True,
                                 help='The rate of the currency to the currency of rate 1.')
    vessel_bol_number = fields.Char(string="B/L Number", readonly=True, store=True)
    related_billing_id = fields.Many2one("freight.billing", string="B/L Number", readonly=True,
                                         compute="_compute_related_billing_id", store=False)
    shipment_etd = fields.Datetime(string="Shipment ETD", readonly=True, store=True,
                                   help="Shipment ETD used to resolve for due date calculation "
                                        "when the customer's Due Date Basis is 'Shipment ETD'.")
    due_date_basis_used = fields.Selection(
        related='partner_id.due_date_basis',
        string='Due Date Basis',
        readonly=True,
        help="From the customer record. Shown here for transparency: if "
             "'Shipment ETD' but no Booking/ETD is set on this invoice, "
             "the Invoice Date is used instead (silent fallback).",
    )
    due_date_basis_note = fields.Char(string="", readonly=True, store=False, default=" (by Invoice Date)",
                                      compute="_compute_due_date_basis_note")

    # Overriding the default attribute to pass the current date function
    invoice_date = fields.Date(default=fields.Date.today)

    @api.depends("vessel_bol_number", "shipment_etd")
    def _compute_related_billing_id(self):
        ''' This compute method makes a clickable link of vessel bol number in
        the accounting module to open the related billing within invoice form '''
        for rec in self:
            rec.related_billing_id = None
            if rec.vessel_bol_number:
                domain = [('vessel_bol_number', '=', rec.vessel_bol_number)]
                billing_id = self.env["freight.billing"].sudo().search(domain, limit=1)
                if billing_id:
                    billing_id['display_name'] = rec.vessel_bol_number
                    rec.related_billing_id = billing_id

                    # ------------------------------------------------------------------
                    # Keep the due date live while still draft if the shipment ETD changes
                    # TODO: due to adding new compute method doesn't trigger when ETD changed
                    # so adding this line code here to recompute invoice_due_date when ETD changed.
                    # Checking context 'allowed_company_ids' to avoid it is recomputed when
                    # create or open an invoice also triggers this method
                    # ------------------------------------------------------------------
                    if not rec.env.context.get("allowed_company_ids"):
                        rec._recompute_payment_terms_lines()

    @api.depends("due_date_basis_used")
    def _compute_due_date_basis_note(self):
        for rec in self:
            rec.due_date_basis_note = " (by Invoice Date)"
            # Without shipment ETD, it will fall back to invoice date, so this note should remain blank
            if rec.due_date_basis_used == "shipment_etd" and rec.shipment_etd:
                rec.due_date_basis_note = " (by Shipment ETD)"
        
    # ------------------------------------------------------------------
    # Hook: let the standard engine run first, then re-anchor on ETD
    # ------------------------------------------------------------------
    def _recompute_payment_terms_lines(self):
        # IMPORTANT: this is the method name in stock Odoo 15 `account.move`
        # that computes date_maturity / invoice_date_due from Invoice Date +
        # Payment Term. Grep your codebase to confirm it hasn't been renamed
        # or wrapped in your fork. If it has, call `_apply_shipment_etd_due_date()`
        # at the end of whichever method currently owns that computation instead
        # (see the note at the bottom of this file).
        res = super()._recompute_payment_terms_lines()
        trigger_fields = self.env.context.get('onchange_trigger_fields') or []
        if 'invoice_date_due' in trigger_fields:
            return res  # the user is editing this field right now — leave it
        self._apply_shipment_etd_due_date()
        return res

    def _apply_shipment_etd_due_date(self):
        """Re-anchor the due date(s) already computed by the standard
        payment-term engine onto the Shipment ETD, preserving each
        instalment's day offset from the reference date.

        Rules encoded here (per client decisions):
        - Only customer invoices / credit notes (out_invoice, out_refund).
        - Only while still draft — due date never moves after posting.
        - Silent fallback to Invoice Date if no booking or no ETD.
        """
        self.ensure_one()

        if self.move_type not in ('out_invoice', 'out_refund'):
            return
        if self.state != 'draft':
            return
        if self.partner_id.due_date_basis != 'shipment_etd':
            return
        if not self.shipment_etd:
            return  # nothing to do — the standard invoice_date-based result stands

        etd_date = self.shipment_etd.date()
        reference_date = self.invoice_date or fields.Date.context_today(self)
        if isinstance(reference_date, str):
            reference_date = fields.Date.from_string(reference_date)

        delta_days = (etd_date - reference_date).days
        if not delta_days:
            return

        # Shift every receivable/payable instalment line by the same number
        # of days, so a split term (e.g. 50% in 10 days / 50% in 30 days)
        # keeps its shape, just re-anchored on ETD instead of Invoice Date.
        term_lines = self.line_ids.filtered(
            lambda l: l.account_id.user_type_id.type in ('receivable', 'payable')
            and l.date_maturity
        )
        for line in term_lines:
            line.date_maturity = line.date_maturity + timedelta(days=delta_days)

        if self.invoice_date_due:
            self.invoice_date_due = self.invoice_date_due + timedelta(days=delta_days)

    def onchange(self, values, field_name, field_onchange):
        return super(
            AccountMove, self.with_context(onchange_trigger_fields=field_name)
        ).onchange(values, field_name, field_onchange)

    @api.depends("related_billing_id")
    def _compute_exchange_rate(self):
        for rec in self:
            rec.exchange_rate = 0.0
            if rec.related_billing_id:
                model = ""
                if rec.is_sale_document(include_receipts=True):     # Customer Invoice
                    model = 'freight.debit.note'
                elif rec.is_purchase_document(include_receipts=True):  # Vendor Bill
                    model = 'freight.credit.note'

                if model:
                    note = self.env[model].sudo().search([
                        ('bill_id', '=', rec.related_billing_id.id)
                    ], limit=1)
                    if note:
                        rec.exchange_rate = note.exchange_rate

    @api.model
    def automate_action_set_bl_number_on_invoice_creation(self, record):
        try:
            if not record:
                return False

            sale_line_ids = record.invoice_line_ids.mapped('sale_line_ids')
            if sale_line_ids:
                sale_order = sale_line_ids[0].order_id
                if sale_order and sale_order.booking_id:
                    record.vessel_bol_number = sale_order.booking_id[0].vessel_bol_no
                    # TODO: Considering refactor method's name to reflect this additional statement
                    record.shipment_etd = sale_order.booking_id[0].etd_revised
            else:
                purchase_order = record.invoice_line_ids.mapped('purchase_order_id')
                if purchase_order:
                    order_name = purchase_order[0].origin
                    sale_order = self.env['sale.order'].sudo().search([('name', '=', order_name)])
                    if sale_order and sale_order[0].booking_id:
                        record.vessel_bol_number = sale_order[0].booking_id[0].vessel_bol_no
                        record.shipment_etd = sale_order[0].booking_id[0].etd_revised

            _logger.info("automate_action_set_bl_number_on_creation executed successful")
        except Exception as e:
            _logger.exception("automate_action_set_bl_number_on_creation - Exception: %s" % e)

    @api.model
    def action_update_debit_note_when_invoice_paid(self, record):
        try:
            if not record:
                return False

            # Flush pending ORM operations to the DB cache within the current transaction
            # Force ORM flush & clear cache to get fresh computed payment_state
            record.env['account.move'].flush(['payment_state'])
            record.invalidate_cache(fnames=['payment_state'])

            _logger.info(
                "action_update_debit_note_when_invoice_paid triggered for record ID %s with payment_state '%s'",
                record.id, record.payment_state
            )

            if record.payment_state not in ('paid', 'in_payment'):
                return False

            _logger.info("action_update_debit_note_when_invoice_paid is triggered")

            odoodbot = self.env.ref('base.user_root')
            self = self.with_user(odoodbot)
            record = record.with_user(odoodbot)

            if not record.vessel_bol_number:
                _logger.info("action_update_debit_note_when_invoice_paid of record ID = %s - vessel_bol_number is empty"
                             , record.id)
                return False

            domain = [('vessel_bol_number', '=', record.vessel_bol_number)]
            related_billing = self.env["freight.billing"].sudo().search(domain, limit=1)
            if not related_billing:
                _logger.info("action_update_debit_note_when_invoice_paid - not found debit note of vessel_bol_number: %s"
                             , record.vessel_bol_number)
                return False

            new_exchange_rate = record.payment_id.exchange_rate
            amount_paid = record.payment_id.amount
            payment_date = record.payment_id.date
            if not new_exchange_rate or not payment_date:
                domain = [('communication', '=', record.name)]
                account_payment_register = self.env["account.payment.register"].sudo().search(domain, limit=1)
                if account_payment_register:
                    new_exchange_rate = account_payment_register.exchange_rate
                    amount_paid = account_payment_register.amount
                    payment_date = account_payment_register.payment_date

            is_both_debit_credit_paid = False
            if new_exchange_rate:
                record.exchange_rate = new_exchange_rate
                domain = [('ref', '=', record.name)]
                account_payment = self.search(domain, limit=1)
                if account_payment:
                    # in some cases, account payment is empty, so update it to have it synced.
                    account_payment.exchange_rate = new_exchange_rate

                notes = None
                if record.is_sale_document(include_receipts=True):  # Customer Invoice
                    notes = related_billing.debit_note_ids
                elif record.is_purchase_document(include_receipts=True):  # Vendor Bill
                    notes = related_billing.credit_note_ids

                if notes:
                    for note in notes:
                        update_change_rate = None
                        if note.amount_total_vnd != amount_paid:
                            '''
                            Re-calculate exchange_rate in debit note to make sure total amount (VND) in debit note
                            matches the amount paid.
                            '''
                            if not note.amount_subtotal_vnd:    # in case of no product item in VND
                                update_change_rate = new_exchange_rate
                            else:
                                amount_vnd_by_usd_exchange = amount_paid - note.amount_subtotal_vnd
                                update_change_rate = amount_vnd_by_usd_exchange / note.amount_total

                        if update_change_rate:
                            note.write({
                                'exchange_rate': update_change_rate,
                                'state': 'completed',
                                'payment_date': payment_date
                            })
                        else:
                            note.write({
                                'state': 'completed',
                                'payment_date': payment_date
                            })


                        if record.is_sale_document(include_receipts=True):  # Debit Note
                            credit_notes = related_billing.credit_note_ids
                            if credit_notes:
                                for credit in credit_notes:
                                    if credit.payment_state == 'paid':  # if credit note already paid before
                                        is_both_debit_credit_paid = True

                        elif record.is_purchase_document(include_receipts=True):    # Credit Note
                            debit_notes = related_billing.debit_note_ids
                            if debit_notes:
                                for debit in debit_notes:
                                    if debit.payment_state == 'paid':  # if debit note already paid before
                                        is_both_debit_credit_paid = True

                        # Update state of booking and bill to 'completed'
                        if is_both_debit_credit_paid:
                            related_billing.with_context(skip_required_validation=True).write({'state': 'completed'})
                            if related_billing.booking_id:
                                stage = self.env["freight.catalog.stage"]\
                                    .sudo().search([('completed', '=', True)], limit=1)
                                if stage:
                                    related_billing.booking_id\
                                        .with_context(skip_required_validation=True).write({'stage_id': stage.id})

            _logger.info("action_update_debit_note_when_invoice_paid executed successful")

            return {
                'related_billing': related_billing,
                'is_both_debit_credit_paid': is_both_debit_credit_paid
            }
        except Exception as e:
            _logger.exception("action_update_debit_note_when_invoice_paid - Exception: %s" % e)

    @api.model
    def action_scheduled_manual_update_states(self):
        ''' Cron '''
        try:
            _logger.info("action_scheduled_manual_update_states is triggered")

            domain = [
                ('payment_state', '=', 'paid')
            ]
            records = self.env['account.move'].sudo().search(domain)

            for rec in records:
                if rec.vessel_bol_number:
                    _logger.info(f"*** processing update states related to account.move with id = {rec.id} ***")

                    domain = [('vessel_bol_number', '=', rec.vessel_bol_number)]
                    related_billing = self.env["freight.billing"].sudo().search(domain, limit=1)

                    if related_billing:
                        is_both_debit_credit_paid = False
                        if rec.is_sale_document(include_receipts=True):  # Customer Invoice
                            debit_notes = related_billing.debit_note_ids
                            if debit_notes:
                                for debit in debit_notes:
                                    if debit.state != 'completed':
                                        debit.write({
                                            'payment_state': 'paid',
                                            'state': 'completed'
                                        })

                            credit_notes = related_billing.credit_note_ids
                            if credit_notes:
                                for credit in credit_notes:
                                    if credit.payment_state == 'paid':
                                        is_both_debit_credit_paid = True

                        elif rec.is_purchase_document(include_receipts=True):  # Vendor Bill
                            credit_notes = related_billing.credit_note_ids
                            if credit_notes:
                                for credit in credit_notes:
                                    if credit.state != 'completed':
                                        credit.write({
                                            'payment_state': 'paid',
                                            'state': 'completed'
                                        })

                            debit_notes = related_billing.debit_note_ids
                            if debit_notes:
                                for debit in debit_notes:
                                    if debit.payment_state == 'paid':
                                        is_both_debit_credit_paid = True

                        # Update state of booking and bill to 'completed'
                        if is_both_debit_credit_paid:
                            related_billing.with_context(skip_required_validation=True).write(
                                {'state': 'completed'})
                            if related_billing.booking_id:
                                stage = self.env["freight.catalog.stage"].sudo().search(
                                    [('completed', '=', True)], limit=1)
                                if stage:
                                    related_billing.booking_id.with_context(skip_required_validation=True)\
                                        .write({'stage_id': stage.id})

            _logger.info("action_scheduled_manual_update_states executed successful")
        except Exception as e:
            _logger.exception("action_scheduled_manual_update_states - Exception: %s" % e)

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        res = super(AccountMove, self).create(vals_list)

        try:
            '''
            Clone attachments from Debit/Credit Note to Invoice/Bill
            '''
            res_id = self.env.context.get("attachment_res_id")
            res_model = self.env.context.get("attachment_res_model")
            if res_id and res_model:
                new_attachments_list = []
                attachments = self.env['ir.attachment'].sudo().search([('res_id', '=', res_id), ('res_model', '=', res_model)])
                if attachments:
                    for att in attachments:
                        new_att = {
                            'res_model': 'account.move',
                            'res_id': res.id,
                            'name': att.name,
                            'company_id': att.company_id.id if att.company_id else False,
                            'type': att.type,
                            'url': att.url,
                            'mimetype': att.mimetype,
                            'store_fname': att.store_fname,
                            'file_size': att.file_size,
                            'checksum': att.checksum
                        }
                        new_attachments_list.append(new_att)

                    if new_attachments_list:
                        self.env['ir.attachment'].create(new_attachments_list)
        except:
            print("ERROR in OVERRIDE create method of account.move which trying clone attachments.")

        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vessel_bol_number = fields.Char(related="move_id.vessel_bol_number", string="B/L Number")
