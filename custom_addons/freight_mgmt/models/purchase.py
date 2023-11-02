# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_round


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_default_exchange_rate(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        vnd_rate = vnd.rate if vnd else 0
        return float_round(vnd_rate, precision_digits=0)

    credit_note_id = fields.One2many('freight.credit.note', 'purchase_order_id',
                                     string='Credit Note Reference', auto_join=True)

    exchange_rate = fields.Float(string='VND/USD rate', default=_get_default_exchange_rate,
                                 help='The rate of VND per USD.', tracking=True, store=True)
    amount_untaxed_usd = fields.Monetary(string='Untaxed Amount (USD)', tracking=True, store=True,
                                         compute='_amount_all_usd_vnd', readonly=True)
    amount_tax_usd = fields.Monetary(string='Taxes (USD)', store=True, readonly=True, compute='_amount_all_usd_vnd')
    amount_total_usd = fields.Monetary(string='Total (USD)', store=True, readonly=True, compute='_amount_all_usd_vnd')

    amount_untaxed_vnd = fields.Monetary(string='Untaxed Amount (VND)', tracking=True, store=True, readonly=True,
                                         compute='_amount_all_usd_vnd', currency_field='vnd_currency_id')
    amount_tax_vnd = fields.Monetary(string='Taxes (VND)', store=True, readonly=True,
                                     compute='_amount_all_usd_vnd', currency_field='vnd_currency_id')
    amount_total_vnd = fields.Monetary(string='Total (VND)', store=True, readonly=True,
                                       compute='_amount_all_usd_vnd', currency_field='vnd_currency_id')
    has_tax_totals_usd = fields.Boolean(compute='_amount_all_usd_vnd')
    has_tax_totals_vnd = fields.Boolean(compute='_amount_all_usd_vnd')

    vnd_currency_id = fields.Many2one('res.currency', 'Vietnamese Currency', compute="_compute_vnd_currency_id")
    total_amount_vnd_summary = fields.Monetary(string='Total Amount (VND)', store=True,
                                               currency_field='vnd_currency_id',
                                               compute='_compute_total_amount_vnd_summary')

    def _compute_vnd_currency_id(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        for rec in self:
            rec.vnd_currency_id = vnd.id or False

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if not self._context.get('validate', False):
            """
            Remove link button 'Create Vendor Bills' displays in action menu when multiple selecting order items. 
            """
            create_vendor_bills_button_id = self.env.ref('purchase.action_purchase_batch_bills').id or False
            for button in res.get('toolbar', {}).get('action', []):
                if create_vendor_bills_button_id and button['id'] == create_vendor_bills_button_id:
                    res['toolbar']['action'].remove(button)

            return res

    @api.depends('amount_total_usd', 'amount_total_vnd', 'exchange_rate')
    def _compute_total_amount_vnd_summary(self):
        for rec in self:
            rec.total_amount_vnd_summary = rec.amount_total_usd * rec.exchange_rate + rec.amount_total_vnd

    @api.depends('amount_untaxed', 'amount_tax', 'amount_total')
    def _amount_all_usd_vnd(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed_usd = amount_tax_usd = 0.0
            amount_untaxed_vnd = amount_tax_vnd = 0.0
            order_line_usd_only = []
            order_line_vnd_only = []
            for line in order.order_line:
                if line.order_line_currency_id and line.order_line_currency_id.name == 'VND':
                    amount_untaxed_vnd += line.price_subtotal_display
                    amount_tax_vnd += line.price_tax_vnd
                    order_line_vnd_only.append(line)
                else:
                    amount_untaxed_usd += line.price_subtotal
                    amount_tax_usd += line.price_tax
                    order_line_usd_only.append(line)

            order.update({
                'amount_untaxed_usd': amount_untaxed_usd,
                'amount_tax_usd': amount_tax_usd,
                'amount_total_usd': amount_untaxed_usd + amount_tax_usd,
                'amount_untaxed_vnd': amount_untaxed_vnd,
                'amount_tax_vnd': amount_tax_vnd,
                'amount_total_vnd': amount_untaxed_vnd + amount_tax_vnd,
                'has_tax_totals_usd': len(order_line_usd_only) > 0,
                'has_tax_totals_vnd': len(order_line_vnd_only) > 0,
            })

    def update_exchange_rate(self):
        self.ensure_one()
        self.exchange_rate = self._get_default_exchange_rate()

    def recalculate_margin(self):
        for rec in self:
            if rec.origin:
                sale_order = self.env["sale.order"].sudo().search([("name", "=", rec.origin)])
                if sale_order:
                    print("Automated execute the recompute_margin action of Sale Order - " + sale_order.name)
                    sale_order.recompute_margin()
