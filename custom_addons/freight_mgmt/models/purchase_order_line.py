# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    exchange_rate = fields.Float(related="order_id.exchange_rate")
    price_unit_input = fields.Float('Unit Price', readonly=False, compute="_compute_price_unit_input",
                                    digits='Product Price', tracking=True, store=True,
                                    help="Input either USD or VND based on selected currency.")
    price_tax_vnd = fields.Monetary(compute='_compute_amount_display', string='Total Tax', store=True, readonly=False)
    price_subtotal_display = fields.Monetary(compute='_compute_amount_display', string='Subtotal', store=True)
    price_total_display = fields.Monetary(compute='_compute_amount_display', string='Total', store=True, readonly=False)
    order_line_currency_id = fields.Many2one('res.currency', 'Currency', tracking=True,
                                             compute="_compute_product_id_changed", store=True, readonly=False)

    @api.onchange('price_unit_input')
    def _onchange_price_unit_input(self):
        if self.order_line_currency_id and self.order_line_currency_id.name == 'VND':
            self.price_unit = self.price_unit_input / self.exchange_rate if self.exchange_rate else 0.0
        else:
            self.price_unit = self.price_unit_input

    @api.depends('order_line_currency_id', 'product_uom', 'product_qty', 'exchange_rate')
    def _compute_price_unit_input(self):
        for rec in self:
            if rec.order_line_currency_id and rec.order_line_currency_id.name == 'VND':
                rec.price_unit_input = rec.price_unit * rec.exchange_rate
            else:
                rec.price_unit_input = rec.price_unit

    @api.depends('product_id')
    def _compute_product_id_changed(self):
        for rec in self:
            rec.order_line_currency_id = rec.product_id.product_currency_id

    @api.depends('price_subtotal', 'price_unit_input', 'product_qty')
    def _compute_amount_display(self):
        for rec in self:
            price_tax_vnd = 0.0
            if rec.order_line_currency_id and rec.order_line_currency_id.name == 'VND':
                price_subtotal_display = rec.product_uom_qty * rec.price_unit_input
                if rec.taxes_id:
                    taxes = rec.taxes_id.compute_all(rec.price_unit_input, rec.order_line_currency_id, rec.product_qty,
                                                     product=rec.product_id, partner=rec.order_id.partner_id)
                    price_tax_vnd = taxes['total_included'] - taxes['total_excluded']
                price_total_display = price_subtotal_display + price_tax_vnd
            else:
                price_subtotal_display = rec.price_subtotal
                price_total_display = rec.price_total

            rec.update({
                'price_subtotal_display': price_subtotal_display,
                'price_tax_vnd': price_tax_vnd,
                'price_total_display': price_total_display,
            })
