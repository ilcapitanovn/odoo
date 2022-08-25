# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    booking_status = fields.Selection([
        ('booked', 'Booking Created'),
        ('to booking', 'To Booking'),
        ('no', 'Nothing to Booking')
    ], string='Booking Status', compute='_get_booking_status', store=True)

    order_type = fields.Selection([
        ('freehand', 'Freehand'),
        ('nominated', 'Nominated'),
    ], string='Order Type', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

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

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrder, self).default_get(fields_list)
        res.update({
            'order_type': 'freehand' or False
        })
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
        - to booking: if any SO line is 'to booking', the whole SO is 'to booking'
        - booked: if all SO lines are booked, the SO is booked.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done'])
        unconfirmed_orders.booking_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return

        for order in confirmed_orders:
            if order.booking_status != 'booked' and order.booking_status != 'to booking':
                if order.invoice_status == 'to invoice' or order.invoice_status == 'invoiced':
                    order.booking_status = 'to booking'
                else:
                    order.booking_status = 'no'
            # if order.state not in ('sale', 'done'):
            #     order.booking_status = 'no'
            # elif not order.booking_status:
            #     order.booking_status = 'no'
            # else:
            #     order.booking_status = 'no'
