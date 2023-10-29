from odoo import fields, models


class FreightLangSonSaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_booking_values(self, order):
        booking_values = super(FreightLangSonSaleOrder, self)._prepare_booking_values(order)

        if self._context.get('branch_code') == 'LS':
            if booking_values:
                booking_values['booking_type'] = 'trading'
                booking_values['transport_type'] = 'land'

        return booking_values
