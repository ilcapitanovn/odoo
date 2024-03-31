from odoo import api, fields, models


class FreightLangSonPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    order_items_saigon = fields.One2many('purchase.order.line.saigon', 'order_id', string='Purchase Order Lines SaiGon',
                                         states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
                                         store=True, copy=True, tracking=True, auto_join=True)

    branch_id_langson_condition = fields.Boolean(compute="_compute_branch_id_langson_condition", readonly=True,
                                                 store=False)

    '''Only computing fields, no need to save db'''
    saigon_amount_untaxed_usd = fields.Monetary(string='Untaxed Amount (USD)', compute='_saigon_amount_totals')
    saigon_amount_tax_usd = fields.Monetary(string='Taxes (USD)', compute='_saigon_amount_totals')
    saigon_amount_total_usd = fields.Monetary(string='Total (USD)', compute='_saigon_amount_totals')

    saigon_amount_untaxed_vnd = fields.Monetary(string='Untaxed Amount (VND)', compute='_saigon_amount_totals',
                                                currency_field='vnd_currency_id')
    saigon_amount_tax_vnd = fields.Monetary(string='Taxes (VND)', compute='_saigon_amount_totals',
                                            currency_field='vnd_currency_id')
    saigon_amount_total_vnd = fields.Monetary(string='Total (VND)', compute='_saigon_amount_totals',
                                              currency_field='vnd_currency_id')
    saigon_has_tax_totals_usd = fields.Boolean(compute='_saigon_amount_totals')
    saigon_has_tax_totals_vnd = fields.Boolean(compute='_saigon_amount_totals')

    saigon_amount_untaxed_vnd_summary = fields.Monetary(string='Total Amount Untaxed (VND)',
                                                        currency_field='vnd_currency_id',
                                                        compute='_saigon_total_amount_vnd_summary')
    saigon_total_amount_vnd_summary = fields.Monetary(string='Total Amount (VND)',
                                                      currency_field='vnd_currency_id',
                                                      compute='_saigon_total_amount_vnd_summary')

    def button_confirm(self):
        self._copy_products_to_saigon()

        return super().button_confirm()

    '''TODO: need to be delete after this function is deployed to production '''
    def action_copy_all_old_order_lines_to_saigon(self):
        branch_langson = self.env.ref('seenpo_multi_branch_base.seenpo_branch_langson', False)
        branch_langson_id = branch_langson.id if branch_langson else -1
        purchase_orders_langson = self.env["purchase.order"].sudo().search([("branch_id", "=", branch_langson_id)])
        if purchase_orders_langson:
            for order in purchase_orders_langson:
                '''Only copy the old ones which are empty '''
                if order.order_line and not order.order_items_saigon:
                    order.copy_products()

    '''Manual copy action to duplicate line of products into SaiGon section'''
    def copy_products(self):
        self._copy_products_to_saigon()

    def _copy_products_to_saigon(self):
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
            "taxes_id": [(6, 0, [x.id for x in item.taxes_id])],
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
            purchase_order_branch_id = rec.branch_id.id if rec.branch_id else -2
            rec.branch_id_langson_condition = purchase_order_branch_id == branch_langson_id

    @api.depends('order_items_saigon.price_total')
    def _saigon_amount_totals(self):
        """
        Compute the total amounts of the Purchase Order for SaiGon section.
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
