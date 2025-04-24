import json

from odoo import api, fields, models


class FreightLangSonSaleOrder(models.Model):
    _inherit = "sale.order"

    order_items_saigon = fields.One2many('sale.order.line.saigon', 'order_id', string='Order Lines SaiGon',
                                         states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
                                         store=True, copy=True, auto_join=True)

    branch_id_langson_condition = fields.Boolean(compute="_compute_branch_id_langson_condition", readonly=True, store=False)

    '''Only computing fields, no need to save db'''
    saigon_amount_untaxed_usd = fields.Monetary(string='Untaxed Amount (USD)', compute='_saigon_amount_totals', store=False)
    saigon_amount_tax_usd = fields.Monetary(string='Taxes (USD)', compute='_saigon_amount_totals', store=False)
    saigon_amount_total_usd = fields.Monetary(string='Total (USD)', compute='_saigon_amount_totals', store=False)

    saigon_amount_untaxed_vnd = fields.Monetary(string='Untaxed Amount (VND)', compute='_saigon_amount_totals',
                                                currency_field='vnd_currency_id', store=False)
    saigon_amount_tax_vnd = fields.Monetary(string='Taxes (VND)', compute='_saigon_amount_totals',
                                            currency_field='vnd_currency_id', store=False)
    saigon_amount_total_vnd = fields.Monetary(string='Total (VND)', compute='_saigon_amount_totals',
                                              currency_field='vnd_currency_id', store=False)
    saigon_has_tax_totals_usd = fields.Boolean(compute='_saigon_amount_totals', store=False)
    saigon_has_tax_totals_vnd = fields.Boolean(compute='_saigon_amount_totals', store=False)

    saigon_amount_untaxed_vnd_summary = fields.Monetary(string='Total Amount Untaxed (VND)', store=False,
                                                        currency_field='vnd_currency_id',
                                                        compute='_saigon_total_amount_vnd_summary')
    saigon_total_amount_vnd_summary = fields.Monetary(string='Total Amount (VND)', store=False,
                                                      currency_field='vnd_currency_id',
                                                      compute='_saigon_total_amount_vnd_summary')

    saigon_margin = fields.Monetary(string="Margin", compute='_compute_saigon_margin', store=False)
    saigon_margin_percent = fields.Float(string="Margin (%)", compute='_compute_saigon_margin', digits=(12, 4), store=False)

    def _prepare_booking_values(self, order):
        booking_values = super(FreightLangSonSaleOrder, self)._prepare_booking_values(order)

        if self._context.get('branch_code') == 'LS':
            if booking_values:
                booking_values['booking_type'] = 'trading'
                booking_values['transport_type'] = 'land'

        return booking_values

    def action_confirm(self):
        self._copy_order_lines_to_saigon()

        return super().action_confirm()

    '''TODO: need to be delete after this function is deployed to production '''
    def action_copy_all_old_order_lines_to_saigon(self):
        branch_langson = self.env.ref('seenpo_multi_branch_base.seenpo_branch_langson', False)
        branch_langson_id = branch_langson.id if branch_langson else -1
        sale_orders_langson = self.env["sale.order"].sudo().search([("branch_id", "=", branch_langson_id)])
        if sale_orders_langson:
            for order in sale_orders_langson:
                '''Only copy the old ones which are empty '''
                if order.order_line and not order.order_items_saigon:
                    order.copy_order_lines()

    '''Manual copy action to duplicate order lines into SaiGon section'''
    def copy_order_lines(self):
        self._copy_order_lines_to_saigon()

    def _copy_order_lines_to_saigon(self):
        items = []
        '''Delete existing records'''
        if self.order_items_saigon:
            for existing_item in self.order_items_saigon:
                items.append((2, existing_item.id))
        '''Then create new records'''
        if self.order_line:
            for item in self.order_line:
                vals = self._prepare_order_line_saigon(item)
                items.append((0, 0, vals))

        if items:
            self.write({'order_items_saigon': items})

    def _prepare_order_line_saigon(self, item):
        vals = {
            "order_id": self.id,
            "external_id": item.id,
            "sequence": item.sequence,
            "name": item.name,
            "product_id": item.product_id.id,
            "product_qty": item.product_uom_qty,
            "product_uom": item.product_uom.display_name,
            "price_unit": item.price_unit_input,
            "taxes_id": [(6, 0, [x.id for x in item.tax_id])],
            "currency_id": item.order_line_currency_id.id if item.order_line_currency_id else False,
            "price_subtotal": item.price_subtotal_display,
            "price_total": item.price_total_display,
        }
        return vals

    @api.depends("branch_id")
    def _compute_branch_id_langson_condition(self):
        branch_langson = self.env.ref('seenpo_multi_branch_base.seenpo_branch_langson', False)
        branch_langson_id = branch_langson.id if branch_langson else -1
        for rec in self:
            order_branch_id = rec.branch_id.id if rec.branch_id else -2
            rec.branch_id_langson_condition = order_branch_id == branch_langson_id

    @api.depends('order_items_saigon.price_total')
    def _saigon_amount_totals(self):
        """
        Compute the total amounts of the Sale Order for SaiGon section.
        """
        for order in self:
            amount_untaxed_usd = amount_tax_usd = 0.0
            amount_untaxed_vnd = amount_tax_vnd = 0.0
            order_line_usd_only = []
            order_line_vnd_only = []
            for line in order.order_items_saigon:
                if line.currency_id and line.currency_id.name == 'VND':
                    amount_untaxed_vnd += line.price_subtotal
                    amount_tax_vnd += line.price_tax
                    order_line_vnd_only.append(line)
                else:
                    amount_untaxed_usd += line.price_subtotal
                    amount_tax_usd += line.price_tax
                    order_line_usd_only.append(line)

            order.update({
                'saigon_amount_untaxed_usd': amount_untaxed_usd,
                'saigon_amount_tax_usd': amount_tax_usd,
                'saigon_amount_total_usd': amount_untaxed_usd + amount_tax_usd,
                'saigon_amount_untaxed_vnd': amount_untaxed_vnd,
                'saigon_amount_tax_vnd': amount_tax_vnd,
                'saigon_amount_total_vnd': amount_untaxed_vnd + amount_tax_vnd,
                'saigon_has_tax_totals_usd': len(order_line_usd_only) > 0,
                'saigon_has_tax_totals_vnd': len(order_line_vnd_only) > 0,
            })

    @api.depends('saigon_amount_total_usd', 'saigon_amount_total_vnd', 'exchange_rate')
    def _saigon_total_amount_vnd_summary(self):
        for rec in self:
            rec.saigon_amount_untaxed_vnd_summary = rec.saigon_amount_untaxed_usd * rec.exchange_rate + rec.saigon_amount_untaxed_vnd
            rec.saigon_total_amount_vnd_summary = rec.saigon_amount_total_usd * rec.exchange_rate + rec.saigon_amount_total_vnd

    @api.depends('saigon_amount_untaxed_vnd_summary')
    def _compute_saigon_margin(self):
        print("_compute_saigon_margin called with order_name = %s" % self.name)

        related_purchase_orders = self.env["purchase.order"].sudo().search([("origin", "=", self.name)])
        for so in self:
            so_commission_total_vnd = so.commission_total * so.exchange_rate if so.commission_total > 0 else 0.0
            po_total_amount_untaxed_vnd = 0.0
            so.saigon_margin = 0
            so.saigon_margin_percent = 0
            if related_purchase_orders:
                for po in related_purchase_orders:
                    if po.state not in ('purchase', 'done'):
                        continue

                    po_total_amount_untaxed_vnd += po.saigon_amount_untaxed_vnd_summary
                    if po.commission_total > 0:
                        po_total_amount_untaxed_vnd += po.commission_total * so.exchange_rate

                if po_total_amount_untaxed_vnd > 0:
                    saigon_margin_vnd = so.saigon_amount_untaxed_vnd_summary - so_commission_total_vnd - po_total_amount_untaxed_vnd
                else:
                    """
                    In case of PO not in purchase or done, then margin of saigon price will be based on margin in normal price
                    """
                    saigon_margin_vnd = (so.saigon_total_amount_vnd_summary - so.total_amount_vnd_summary) + so.margin * so.exchange_rate

                so.saigon_margin = saigon_margin_vnd / so.exchange_rate
                so.saigon_margin_percent = so.saigon_amount_untaxed_vnd_summary and saigon_margin_vnd / so.saigon_amount_untaxed_vnd_summary

