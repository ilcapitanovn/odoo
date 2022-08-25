# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_round


class FreightCreditNoteItem(models.Model):
    _name = 'freight.credit.note.item'
    _description = 'Freight Credit Note Item'
    _order = 'sequence, id'
    _check_company_auto = True

    credit_id = fields.Many2one('freight.credit.note', string='Credit Note', required=True, ondelete='cascade',
                               index=True, copy=False)

    external_id = fields.Integer(string="Related Purchase Order Line ID", store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Text(string='Item Name')
    quantity = fields.Float(string="Quantity")
    uom = fields.Text(string='Unit Of Measure')
    unit_price = fields.Text(string='Price')
    currency_id = fields.Many2one(related='credit_id.currency_id', depends=['credit_id.currency_id'], store=True,
                                  string='Currency')
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False}, store=True)
    tax_amount = fields.Float(related="tax_id.amount", string="Tax Amount")
    tax_amount_percent = fields.Char(compute="_format_tax_amount", string="VAT TAX")
    price_subtotal = fields.Monetary(string='Subtotal', store=True)
    price_tax = fields.Float(string='Total Tax', store=True)
    price_total = fields.Monetary(string='Total', store=True)

    company_id = fields.Many2one(related='credit_id.company_id', string='Company', store=True, index=True)

    state = fields.Selection(
        related='credit_id.state', string='Debit Status', copy=False, store=True)

    @api.depends('quantity', 'unit_price', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO/Debit item.
        """
        for item in self:
            price = item.unit_price
            taxes = item.tax_id.compute_all(price, item.credit_id.currency_id, item.quantity)

            item.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('tax_id')
    def _format_tax_amount(self):
        for rec in self:
            if rec.tax_id:
                rec.tax_amount_percent = '%s%%' % float_round(rec.tax_id.amount, precision_digits=0)
            else:
                rec.tax_amount_percent = ''