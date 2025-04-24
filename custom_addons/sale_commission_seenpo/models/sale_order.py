# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('commission_total')
    def _compute_margin(self):
        super(SaleOrder, self)._compute_margin()
        for order in self:
            new_margin = order.margin - order.commission_total
            '''
            Deduce commission total from Purchase Order if any
            '''
            purchase_orders = self.env["purchase.order"].sudo().search([("origin", "=", order.name)])
            if purchase_orders:
                for po in purchase_orders:
                    if po.state not in ('purchase', 'done'):
                        continue

                    if po.commission_total > 0:
                        new_margin -= po.commission_total
            if 'profit_sharing_percentage' in order and order.profit_sharing_percentage > 0:
                new_margin = new_margin * (100 - order.profit_sharing_percentage) / 100
            order.margin = new_margin
            order.margin_percent = order.amount_untaxed and order.margin / order.amount_untaxed

    def _compute_commission_total(self):
        for record in self:
            """ If there are changes in the existing lines then override this compute method
            to calculate commission_total. This fixing an issue which is loading the old price,
            instead of the new prices.
            If those are changes in new lines then pass it to super method processing
            """
            # new_price_subtotal = record.mapped("order_line.price_subtotal")
            # existing_price_subtotal = record.mapped("order_line.agent_ids.object_id.price_subtotal")

            # if new_price_subtotal == existing_price_subtotal:
            #     super(SaleOrder, self)._compute_commission_total()
            #     record.commission_total = sum(record.mapped("order_line.agent_ids.amount_custom"))
            # else:
            commission_total = 0.0
            for order_line in self.order_line:
                if order_line.agent_ids:
                    for agent_line in order_line.agent_ids:
                        amount = agent_line.amount_custom
                        if amount <= 0:
                            amount = agent_line._get_commission_amount(
                                agent_line.commission_id,
                                order_line.price_subtotal,
                                order_line.product_id,
                                order_line.product_uom_qty,
                            )
                        commission_total += amount

            if commission_total >= 0 and commission_total != record.commission_total:
                record.commission_total = commission_total


class SaleOrderLineAgent(models.Model):
    _inherit = "sale.order.line.agent"
    _description = "Agent detail of commission line in order lines"

    amount_custom = fields.Float(string="Commission Amount Custom", default=0.0,
                                 store=True, tracking=True)

    @api.constrains('amount_custom')
    def _check_amount_custom(self):
        for rec in self:
            amount_max = rec._get_commission_amount_max()
            if amount_max < rec.amount_custom:
                raise ValidationError(_("The commission custom amount must be less than the maximum amount of %s."
                                        % amount_max))

    @api.onchange("amount_custom")
    def _onchange_amount_custom(self):
        if self.amount_custom < 0:
            raise UserError(_("The commission amount must be positive."))
            self.amount_custom = 0
        else:
            amount_max = self._get_commission_amount_max()
            if amount_max < self.amount_custom:
                raise ValidationError(_("The commission custom amount must be less than the maximum amount of %s."
                                        % amount_max))

    def _get_commission_amount_max(self):
        amount_max = 0.0
        if self.commission_id and self.commission_id.commission_type == "fixed" and self.commission_id.fix_qty_max > 0:
            """
            Check custom amount if it exceeds fixed maximum
            """
            subtotal = self.object_id.price_subtotal
            if self.commission_id.amount_base_type == "net_amount":
                # If subtotal (sale_price * quantity) is less than
                # standard_price * quantity, it means that we are selling at
                # lower price than we bought, so set amount_base to 0
                # subtotal = max([0, subtotal - self.object_id.product_id.standard_price * self.object_id.product_uom_qty])
                """
                Changed on 2024/01/25: because cost of product (standard price) is not used to calculate margin, but
                it's total of purchase amount, so selling at lower price is not suitable in this case. Let's user
                decides based on subtotal for clear.
                """
                subtotal = max([0, subtotal])
            amount_max = subtotal * (self.commission_id.fix_qty_max / 100.0)
        return amount_max
