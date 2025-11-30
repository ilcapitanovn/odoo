# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models
from odoo.tools import float_round


_logger = logging.getLogger(__name__)


class FreightAccountPayment(models.Model):
    _inherit = "account.payment"

    vessel_bol_number = fields.Char(compute="_compute_vessel_bol_number", string="B/L Number",
                                    readonly=True, store=False)

    @api.depends("move_id.related_billing_id")
    def _compute_vessel_bol_number(self):
        for rec in self:
            rec.vessel_bol_number = ""
            if rec.move_id and rec.move_id.related_billing_id:
                bill = rec.move_id.related_billing_id
                rec.vessel_bol_number = bill.vessel_bol_number if bill.vessel_bol_number else bill.vessel_booking_number


class FreightAccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_default_exchange_rate(self):
        vnd_rate = 0
        invoice_id = self.env.context.get('active_id')
        if invoice_id:
            move = self.env['account.move'].sudo().search([('id', '=', invoice_id)], limit=1)
            if move and move.vessel_bol_number:
                billing = self.env['freight.billing'].sudo().search([
                    ('vessel_bol_number', '=', move.vessel_bol_number)
                ], limit=1)
                if billing:
                    model = ""
                    if move.is_sale_document(include_receipts=True):  # Customer Invoice
                        model = 'freight.debit.note'
                    elif move.is_purchase_document(include_receipts=True):  # Vendor Bill
                        model = 'freight.credit.note'

                    if model:
                        note = self.env[model].sudo().search([
                            ('bill_id', '=', billing.id)
                        ], limit=1)
                        if note:
                            vnd_rate = note.exchange_rate

        if not vnd_rate:
            vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
            vnd_rate = vnd.rate if vnd else 0

        return float_round(vnd_rate, precision_digits=0)

    # == Payment custom fields ==
    currency_name = fields.Char(related='currency_id.name')
    exchange_rate = fields.Float(string='Exchange rate', readonly=False,
                                 default=_get_default_exchange_rate,
                                 required=True, tracking=True, store=True,
                                 help='The rate of the currency to the currency of rate 1.')

    def _create_payment_vals_from_wizard(self):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_wizard()
        # Update exchange_rate from payment register wizard into account.payment model
        # for retrieving later when need to update debit note in freight.
        payment_vals.update({'exchange_rate': self.exchange_rate})
        return payment_vals

    def _compute_currency_id(self):
        """
        Override parent method to set default currency is VND when loading payment wizard
        """
        for wizard in self:
            # try to return VND first
            vnd = self.env['res.currency'].search([('name', '=', 'VND')], limit=1)
            if vnd:
                wizard.currency_id = vnd
            else:
                # fallback: current logic from Odoo community guidance
                super()._compute_currency_id()

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id',
                 'payment_date', 'exchange_rate')
    def _compute_amount(self):
        self.ensure_one()
        super()._compute_amount()

        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.source_amount * wizard.exchange_rate
                wizard.amount = amount_payment_currency

    @api.depends('amount')
    def _compute_payment_difference(self):
        """
        Set difference constantly zero to skip checking different
        """
        self.ensure_one()
        super()._compute_payment_difference()

        for wizard in self:
            wizard.payment_difference = 0

    @api.onchange("amount")
    def _onchange_amount(self):
        if self.currency_id and self.currency_id.name == 'VND':
            if self.source_amount_currency:
                new_exchange_rate = self.amount / self.source_amount_currency
                self.exchange_rate = new_exchange_rate

    def update_exchange_rate(self):
        self.ensure_one()
        ''' When user clicks refresh to update exchange rate, it should be loaded from the current exchange
        rates where these rates are updated from Vietcombank API via automated action'''
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        self.exchange_rate = vnd.rate if vnd else 0

        # IMPORTANT: return an action to reload the same wizard - keep wizard opening
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',  # keep it as a popup
        }
