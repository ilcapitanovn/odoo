# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

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

    @api.depends("vessel_bol_number")
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
            else:
                purchase_order = record.invoice_line_ids.mapped('purchase_order_id')
                if purchase_order:
                    order_name = purchase_order[0].origin
                    sale_order = self.env['sale.order'].sudo().search([('name', '=', order_name)])
                    if sale_order and sale_order[0].booking_id:
                        record.vessel_bol_number = sale_order[0].booking_id[0].vessel_bol_no

            _logger.info("automate_action_set_bl_number_on_creation executed successful")
        except Exception as e:
            _logger.exception("automate_action_set_bl_number_on_creation - Exception: %s" % e)

    @api.model
    def action_update_debit_note_when_invoice_paid(self, record):
        try:
            if not record or record.payment_state != "paid":
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

                        is_both_debit_credit_paid = False
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
