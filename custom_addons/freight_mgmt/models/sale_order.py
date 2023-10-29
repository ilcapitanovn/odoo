# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_default_exchange_rate(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        vnd_rate = vnd.rate if vnd else 0
        return float_round(vnd_rate, precision_digits=0)

    booking_id = fields.One2many('freight.booking', 'order_id', string='Booking Reference', auto_join=True)
    booking_status = fields.Selection([
        ('booked', 'Booking Created'),
        ('to booking', 'To Booking'),
        ('no', 'Nothing to Booking')
    ], string='Booking Status', compute='_get_booking_status', store=True)

    order_type = fields.Selection([
        ('freehand', 'Freehand'),
        ('nominated', 'Nominated'),
    ], string='Order Type', readonly=True, tracking=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    order_shipment_type = fields.Selection(
        selection=[("fcl-exp", "FCL Export"), ("fcl-imp", "FCL Import"), ("lcl-exp", "LCL Export"),
                   ("lcl-imp", "LCL Import"), ("air-imp", "Air Import"), ("air-exp", "Air Export")],
        string="Shipment Type", states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        readonly=True, default="fcl-exp", tracking=True, help='Type of Shipment')

    profit_sharing_percentage = fields.Float(
        string="Profit Sharing (%)",
        help="The margin will be shared by this percentage to the nominated order",
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    exchange_rate = fields.Float(string='VND/USD rate', default=_get_default_exchange_rate,
                                 help='The rate of VND per USD.', tracking=True, store=True)
    amount_untaxed_usd = fields.Monetary(string='Untaxed Amount (USD)', store=True, compute='_amount_all_usd_vnd')
    amount_tax_usd = fields.Monetary(string='Taxes (USD)', store=True, compute='_amount_all_usd_vnd')
    amount_total_usd = fields.Monetary(string='Total (USD)', store=True, compute='_amount_all_usd_vnd')

    amount_untaxed_vnd = fields.Monetary(string='Untaxed Amount (VND)', store=True, compute='_amount_all_usd_vnd',
                                         currency_field='vnd_currency_id')
    amount_tax_vnd = fields.Monetary(string='Taxes (VND)', store=True, compute='_amount_all_usd_vnd',
                                     currency_field='vnd_currency_id')
    amount_total_vnd = fields.Monetary(string='Total (VND)', store=True, compute='_amount_all_usd_vnd',
                                       currency_field='vnd_currency_id')
    has_tax_totals_usd = fields.Boolean(compute='_amount_all_usd_vnd')
    has_tax_totals_vnd = fields.Boolean(compute='_amount_all_usd_vnd')

    vnd_currency_id = fields.Many2one('res.currency', 'Vietnamese Currency', compute="_compute_vnd_currency_id")
    total_amount_vnd_summary = fields.Monetary(string='Total Amount (VND)', store=True,
                                               currency_field='vnd_currency_id',
                                               compute='_compute_total_amount_vnd_summary')

    def update_exchange_rate(self):
        self.ensure_one()
        self.exchange_rate = self._get_default_exchange_rate()

    def _compute_vnd_currency_id(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        for rec in self:
            rec.vnd_currency_id = vnd.id or False

    @api.depends('amount_total_usd', 'amount_total_vnd', 'exchange_rate')
    def _compute_total_amount_vnd_summary(self):
        for rec in self:
            rec.total_amount_vnd_summary = rec.amount_total_usd * rec.exchange_rate + rec.amount_total_vnd

    @api.depends('amount_untaxed', 'amount_tax', 'amount_total', 'exchange_rate')
    def _amount_all_usd_vnd(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            amount_untaxed_vnd = amount_tax_vnd = 0.0
            order_line_usd_only = []
            order_line_vnd_only = []
            for line in order.order_line:
                if line.order_line_currency_id and line.order_line_currency_id.name == 'VND':
                    amount_untaxed_vnd += line.price_subtotal_display
                    amount_tax_vnd += line.price_tax_vnd
                    order_line_vnd_only.append(line)
                else:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                    order_line_usd_only.append(line)

            order.update({
                'amount_untaxed_usd': amount_untaxed,
                'amount_tax_usd': amount_tax,
                'amount_total_usd': amount_untaxed + amount_tax,
                'amount_untaxed_vnd': amount_untaxed_vnd,
                'amount_tax_vnd': amount_tax_vnd,
                'amount_total_vnd': amount_untaxed_vnd + amount_tax_vnd,
                'has_tax_totals_usd': len(order_line_usd_only) > 0,
                'has_tax_totals_vnd': len(order_line_vnd_only) > 0,
            })

    def recompute_margin(self):
        '''
        Update purchase price by the latest price unit from purchase order line if there is different
        so that recalculate profit will get the latest values
        '''
        # related_purchase_orders = self._get_purchase_orders()
        related_purchase_orders = self.env["purchase.order"].sudo().search([("origin", "=", self.name)])
        if related_purchase_orders:
            for so_line in self.order_line:
                for po in related_purchase_orders:
                    if po.state == 'cancel':
                        continue

                    for po_line in po.order_line:
                        if po_line.product_id and so_line.product_id and po_line.product_id.id == so_line.product_id.id \
                                and po_line.price_unit != so_line.purchase_price:
                            so_line.purchase_price = po_line.price_unit
        # else -> skip if a sale order doesn't have a related purchase order

        super(SaleOrder, self)._compute_margin()
        self.message_post(body="Tính lại biên lợi nhuận")

    def create_bookings(self):
        """
        Create one or multi bookings from tree view when
        One: user click 'Create Booking' button
        Multiple: user selects checkboxes and click 'Create Bookings' in Actions
        """
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = self.id

        sale_orders = self.env['sale.order'].browse(active_ids)

        new_bookings = None
        if sale_orders:
            new_bookings = sale_orders._create_bookings()

        if new_bookings:
            for order in sale_orders:
                order.booking_status = 'booked'

            return self._open_view_booking(new_bookings)

    def _open_view_booking(self, new_bookings):
        booking_form = self.env.ref('freight_mgmt.freight_booking_view_form', False)

        if isinstance(new_bookings.ids, list):
            new_booking_id = new_bookings.ids[0]
        else:
            new_booking_id = new_bookings.id

        if booking_form and new_booking_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'freight.booking',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'views': [(booking_form.id, 'form')],
                'view_id': booking_form.id,
                'res_id': new_booking_id,
            }

    def _create_bookings(self):
        # 1) Create bookings.
        booking_vals_list = []
        for order in self:
            order = order.with_company(order.company_id)
            booking_vals = self._prepare_booking_values(order)

            booking_vals_list.append(booking_vals)

        if not booking_vals_list:
            raise self._nothing_to_invoice_error()

        bookings = self.env['freight.booking'].sudo().with_context().create(booking_vals_list)

        return bookings

    def _prepare_booking_values(self, order):
        booking_vals = {
            'order_id': order.id,
            'user_id': order.user_id.id,
            'partner_id': order.partner_id.id,
            'order_type': order.order_type
        }

        return booking_vals

    def action_view_purchase_orders(self):
        self.ensure_one()
        # purchase_order_ids = self._get_purchase_orders().ids
        purchase_orders = self.env["purchase.order"].search([("origin", "=", self.name)])
        if purchase_orders:
            purchase_order_ids = purchase_orders.ids
        else:
            purchase_order_ids = self._get_purchase_orders().ids
        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
        }
        if len(purchase_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': purchase_order_ids[0],
            })
        else:
            action.update({
                'name': _("Purchase Order generated from %s", self.name),
                'domain': [('id', 'in', purchase_order_ids)],
                'view_mode': 'tree,form',
            })
        return action

    @api.depends('order_line.purchase_line_ids.order_id')
    def _compute_purchase_order_count(self):
        for order in self:
            # order.purchase_order_count = len(order._get_purchase_orders())
            purchase_orders = self.env["purchase.order"].search([("origin", "=", order.name)])
            order.purchase_order_count = len(purchase_orders)

    @api.onchange("order_type")
    def _onchange_order_type(self):
        if self.order_type != 'nominated':
            self.profit_sharing_percentage = 0

    @api.onchange("profit_sharing_percentage")
    def _onchange_profit_sharing_percentage(self):
        if self.order_type == 'nominated':
            if 0 <= self.profit_sharing_percentage <= 100:
                super(SaleOrder, self)._compute_margin()
                # new_margin = self.margin * (100 - self.profit_sharing_percentage) / 100
                # self.margin = new_margin
                # self.margin_percent = self.amount_untaxed and self.margin / self.amount_untaxed
            else:
                raise ValidationError(_("The input value is invalid. The profit sharing percentage must be 0 to 100%."))
        else:
            super(SaleOrder, self)._compute_margin()

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrder, self).default_get(fields_list)
        res.update({
            'order_type': 'freehand' or False
        })
        return res

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     # OVERRIDE to remove readonly state of the order_type field if user logged in is manager.
    #     res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if not self._context.get('validate', False):
            """
            Remove link button 'Create Invoices' displays in action menu when multiple selecting order items. 
            """
            create_invoices_button_id = self.env.ref('sale.action_view_sale_advance_payment_inv').id or False
            for button in res.get('toolbar', {}).get('action', []):
                if create_invoices_button_id and button['id'] == create_invoices_button_id:
                    res['toolbar']['action'].remove(button)

            return res

    @api.model
    def _nothing_to_invoice_error(self):
        return UserError(_(
            "There is nothing to booking!\n\n"
            "Reason(s) of this behavior could be:\n"
            "- You should invoice your orders before booking them: Click on the \"truck\" icon "
            "(top-right of your screen) and follow instructions.\n"
            "- You should modify the booking policy of your order: Open the Freight, go to the "
            "\"Configuration\" tab and modify booking policy from \"Orders\" to \"Invoiced\"."
            " For Services, you should modify the Service Booking Policy to "
            "'Prepaid'."
        ))

    @api.depends('state', 'invoice_status')
    def _get_booking_status(self):
        """
        Compute the booking status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          booking. This is also the default value if the conditions of no other status is met.
        - to booking: based on the whole invoice status, the whole SO is 'to booking'
        - booked: if SO has already created booking and re-confirmed from cancelled SO, the SO is booked.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done'])
        unconfirmed_orders.booking_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return

        for order in confirmed_orders:
            if order.booking_status != 'booked' and order.booking_status != 'to booking':
                if order.booking_id:
                    # In case of SO re-confirmed from a cancelled SO and it has already created booking
                    order.booking_status = 'booked'
                else:
                    if order.invoice_status == 'to invoice' or order.invoice_status == 'invoiced':
                        order.booking_status = 'to booking'
                    else:
                        order.booking_status = 'no'
            elif order.booking_status == 'booked' and not order.booking_id:
                order.booking_status = 'to booking'     # Fix issue SO is lost due to delete related booking
            # if order.state not in ('sale', 'done'):
            #     order.booking_status = 'no'
            # elif not order.booking_status:
            #     order.booking_status = 'no'
            # else:
            #     order.booking_status = 'no'
