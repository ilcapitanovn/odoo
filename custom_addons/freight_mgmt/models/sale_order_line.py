# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import time
from datetime import datetime
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    exchange_rate = fields.Float(related="order_id.exchange_rate")
    price_unit_input = fields.Float('Unit Price', readonly=False, compute="_compute_price_unit_input",
                                    digits='Product Price', store=True, required=True,
                                    help="Input either USD or VND based on selected currency.")
    price_tax_vnd = fields.Monetary(compute='_compute_amount_display', string='Total Tax', store=True, readonly=False)
    price_subtotal_display = fields.Monetary(compute='_compute_amount_display', string='Subtotal', store=True)
    price_total_display = fields.Monetary(compute='_compute_amount_display', string='Total', store=True, readonly=False)
    order_line_currency_id = fields.Many2one('res.currency', 'Currency', tracking=True, required=True,
                                             compute="_compute_product_id_changed", store=True, readonly=False)
    product_is_no_vat = fields.Boolean(compute="_compute_product_is_no_vat")
    purchase_price_custom = fields.Float(
        string='Unit Cost', compute="_compute_purchase_price_custom",
        digits='Product Price', store=True, readonly=True)
    purchase_price_custom_display = fields.Char(
        string="Cost", compute="_compute_purchase_price_custom_display", readonly=True)

    # margin_vnd = fields.Float("Margin", compute='_compute_margin_vnd',
    #                           digits='Product Price', store=True, groups="base.group_user")
    # is_pricelist_price = fields.Selection(
    #     selection=[('undefined', 'Undefined'), ('yes', 'Yes'), ('no', 'No')],
    #     compute='_compute_product_id_changed',
    #     default='undefined', string='Is Pricelist Price', store=True,
    #     help='Flag to determine price from pricelist or product details'
    # )
    # flag_just_updated = fields.Boolean(compute="_compute_flag_just_updated")
    #
    # def _compute_flag_just_updated(self):
    #     self.flag_just_updated = False

    @api.onchange('price_unit_input')
    def _onchange_price_unit_input(self):
        if self.order_line_currency_id and self.order_line_currency_id.name == 'VND':
            self.price_unit = self.price_unit_input / self.exchange_rate if self.exchange_rate else 0.0
        else:
            self.price_unit = self.price_unit_input

    @api.depends("product_id.product_tmpl_id.is_no_vat")
    def _compute_product_is_no_vat(self):
        for rec in self:
            if rec.product_id:
                rec.product_is_no_vat = rec.product_id.product_tmpl_id.is_no_vat
            else:
                rec.product_is_no_vat = False

    @api.depends('purchase_price_custom')
    def _compute_purchase_price_custom_display(self):
        # usd_currency = self.env.ref('base.USD')
        for rec in self:
            rec.purchase_price_custom_display = ""
            if rec.purchase_price_custom == -99:
                rec.purchase_price_custom_display = "N/A"
            elif rec.purchase_price_custom >= 0:
                rec.purchase_price_custom_display = "$ {:,.2f}".format(rec.purchase_price_custom or 0.0)

    @api.depends('purchase_price')
    def _compute_purchase_price_custom(self):
        '''
        purchase_price is calculated in sale_margin at beginning. If a PO linked to SO is confirmed,
        and recalculate_margin happening, then purchase_price_custom is recalculated based on
        PO line price.
        '''
        order_name = ''
        related_purchase_orders = None
        for rec in self:
            purchase_price = rec.purchase_price
            try:
                '''
                Only getting product cost from PO if SO was confirmed
                '''
                if rec.order_id.name in ('S01812', 'S01813', 'S01814'):
                    _logger.info("debugging")

                if not order_name:
                    order_name = rec.order_id.name
                if order_name != rec.order_id.name:
                    order_name = rec.order_id.name
                    related_purchase_orders = None

                if rec.order_id.state in ('sale', 'done'):
                    if not related_purchase_orders:  # Ensure call one time
                        related_purchase_orders = self.env["purchase.order"].sudo().search([
                            ("origin", "=", order_name),
                            ("state", 'in', ('purchase', 'done'))
                        ])

                    if related_purchase_orders:
                        purchase_price = -99    # In this case, set purchase_price is N/A
                        for po in related_purchase_orders:
                            for po_line in po.order_line:
                                if po_line.sale_line_id and po_line.sale_line_id.id == rec.id \
                                        or po_line.product_id and rec.product_id and po_line.product_id.id == rec.product_id.id:
                                    purchase_price = po_line.price_unit

            except Exception as e:
                _logger.exception("_compute_purchase_price_custom - Exception: %s" % e)

            rec.purchase_price_custom = purchase_price

    # price_unit is set disabled, but it can be changed if user changes pricelist and click
    # 'Update Prices' button
    @api.depends('order_line_currency_id', 'product_uom', 'product_uom_qty', 'exchange_rate')
    def _compute_price_unit_input(self):
        for rec in self:
            if rec.order_line_currency_id and rec.order_line_currency_id.name == 'VND':
                rec.price_unit_input = rec.price_unit * rec.exchange_rate
            else:
                rec.price_unit_input = rec.price_unit

    @api.depends('product_id', 'product_template_id')
    def _compute_product_id_changed(self):
        for rec in self:
            rec.order_line_currency_id = rec.product_template_id.product_currency_id

    def _calculate_amount_display(self):
        rec = self
        price_tax_vnd = 0.0
        if rec.order_line_currency_id and rec.order_line_currency_id.name == 'VND':
            price_subtotal_display = rec.product_uom_qty * rec.price_unit_input
            if rec.tax_id:
                taxes = rec.tax_id.compute_all(rec.price_unit_input, rec.order_line_currency_id,
                                               rec.product_uom_qty, product=rec.product_id,
                                               partner=rec.order_id.partner_shipping_id)
                price_tax_vnd = taxes['total_included'] - taxes['total_excluded']
            price_total_display = price_subtotal_display + price_tax_vnd
        else:
            price_subtotal_display = rec.price_subtotal
            price_total_display = rec.price_total

        return {
            'price_tax_vnd': price_tax_vnd,
            'price_subtotal_display': price_subtotal_display,
            'price_total_display': price_total_display,
        }

    @api.depends('price_subtotal', 'price_unit_input', 'product_uom_qty')
    def _compute_amount_display(self):
        try:
            for rec in self:
                obj = rec._calculate_amount_display()
                rec.update({
                    'price_tax_vnd': obj.get('price_tax_vnd'),
                    'price_subtotal_display': obj.get('price_subtotal_display'),
                    'price_total_display': obj.get('price_total_display'),
                })
        except Exception as e:
            _logger.exception("sale_order_line._compute_amount_display - Exception: %s" % e)

    @api.model
    def action_automate_fix_price_subtotal_display_zero(self):
        """
        TODO: Workaround - a scheduled action to automate fix price_subtotal_display showing zero (0.0)
        for several Sale Order, although price_subtotal and other values are correct
        """
        try:
            domain = [
                ('product_uom_qty', '>', 0),
                ('price_unit_input', '>', 0),
                ('price_subtotal_display', '=', False)
            ]
            lines = self.env['sale.order.line'].sudo().search(domain, limit=500)
            if lines and lines.ids:
                for line in lines:
                    obj = line._calculate_amount_display()
                    line.write({
                        'price_tax_vnd': obj.get('price_tax_vnd'),
                        'price_subtotal_display': obj.get('price_subtotal_display'),
                        'price_total_display': obj.get('price_total_display'),
                    })
                    time.sleep(0.01)

            _logger.info("action_automate_fix_price_subtotal_display_zero - executed successful.")

        except Exception as e:
            _logger.exception("action_automate_fix_price_subtotal_display_zero - Exception: " + str(e))


class SaleOrderLineAgent(models.Model):
    _inherit = "sale.order.line.agent"
