# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_round


class SaleOrderLineSaiGon(models.Model):
    _name = 'sale.order.line.saigon'
    _description = 'Freight LangSon Sale Order Line SaiGon'
    _order = 'sequence, id'
    _check_company_auto = True

    order_id = fields.Many2one('sale.order', string='Order Reference', index=True, required=True,
                               ondelete='cascade')
    external_id = fields.Integer(string="Related Order Line ID", store=True)
    name = fields.Text(string='Product Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    product_uom = fields.Text(string='UoM')
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 change_default=True)
    product_type = fields.Selection(related='product_id.detailed_type', readonly=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)

    currency_id = fields.Many2one("res.currency", store=True, string='Currency')
    company_id = fields.Many2one('res.company', related='order_id.company_id', string='Company', store=True,
                                 readonly=True)
    branch_id = fields.Many2one(related="order_id.branch_id", string='Branch', readonly=True)

    state = fields.Selection(related='order_id.state', store=True)

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        self._calculate_totals()

    @api.onchange("price_unit")
    def _onchange_price_unit(self):
        self._calculate_totals()

    @api.onchange("taxes_id")
    def _onchange_taxes_id(self):
        self._calculate_totals()

    @api.onchange("currency_id")
    def _onchange_currency_id(self):
        if self.order_id.exchange_rate:
            if self.currency_id and self.currency_id.name == 'VND':
                self.price_unit = float_round(self.price_unit * self.order_id.exchange_rate, precision_digits=0)
            elif self.currency_id and self.currency_id.name == 'USD':
                self.price_unit = float_round(self.price_unit / self.order_id.exchange_rate, precision_digits=2)

    def _calculate_totals(self):
        """
        Compute the amounts of the SO line SaiGon
        """
        for item in self:
            price = item.price_unit
            taxes = item.taxes_id.compute_all(price, item.currency_id, item.product_qty)

            item.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })