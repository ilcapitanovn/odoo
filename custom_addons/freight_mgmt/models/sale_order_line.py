# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # def _get_default_price_unit_input(self):
    #     if self.order_line_currency_id and self.order_line_currency_id.name == 'VND':
    #         self.price_unit_input = self.price_unit * self.exchange_rate
    #     else:
    #         self.price_unit_input = self.price_unit

    exchange_rate = fields.Float(related="order_id.exchange_rate")
    price_unit_input = fields.Float('Unit Price', readonly=False, compute="_compute_price_unit_input",
                                    digits='Product Price', store=True, required=True,
                                    help="Input either USD or VND based on selected currency.")
    price_tax_vnd = fields.Monetary(compute='_compute_amount_display', string='Total Tax', store=True, readonly=False)
    price_subtotal_display = fields.Monetary(compute='_compute_amount_display', string='Subtotal', store=True)
    price_total_display = fields.Monetary(compute='_compute_amount_display', string='Total', store=True, readonly=False)
    order_line_currency_id = fields.Many2one('res.currency', 'Currency', tracking=True, required=True,
                                             compute="_compute_product_id_changed", store=True, readonly=False)
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

    @api.depends('price_subtotal', 'price_unit_input', 'product_uom_qty')
    def _compute_amount_display(self):
        for rec in self:
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

            rec.update({
                'price_tax_vnd': price_tax_vnd,
                'price_subtotal_display': price_subtotal_display,
                'price_total_display': price_total_display,
            })

    # @api.depends('margin')
    # def _compute_margin_vnd(self):
    #     for rec in self:
    #         if rec.exchange_rate and rec.margin:
    #             rec.margin_vnd = rec.margin * rec.exchange_rate
    #         else:
    #             rec.margin_vnd = 0.0

    # @staticmethod
    # def _check_price_from_template_or_pricelist(so_line):
    #     result = {'is_price_from_pricelist': False, 'fixed_price_vnd': 0.0}
    #
    #     if so_line.order_id and so_line.order_id.pricelist_id:
    #         for item in so_line.order_id.pricelist_id.item_ids:
    #             if item.product_tmpl_id and so_line.product_template_id.id == item.product_tmpl_id.id:
    #                 if item.fixed_price == so_line.price_unit:
    #                     result['is_price_from_pricelist'] = True
    #                     result['fixed_price_vnd'] = item.fixed_price_vnd
    #                     break
    #
    #     return result
