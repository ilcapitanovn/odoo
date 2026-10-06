# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class FreightCreditBannerController(http.Controller):

    @http.route('/freight_credit_control/dashboard_banner', auth='user', type='json')
    def freight_credit_dashboard_banner(self):
        """Returns the KPI banner shown above the Credit Control Tower kanban
        board (bound via the `banner_route` attribute on that kanban view).
        Unlike Odoo's onboarding banners this one is never dismissed - it is
        a permanent summary, not a one-time setup panel."""
        Booking = request.env['freight.booking']

        blocked_count = Booking.search_count([('credit_hold_state', '=', 'blocked')])
        pending_count = Booking.search_count([('credit_hold_state', '=', 'pending_approval')])
        ready_count = Booking.search_count([('credit_hold_state', '=', 'released')])

        held_bookings = Booking.search([('credit_hold_state', 'in', ('blocked', 'pending_approval'))])
        overdue_amount = sum(held_bookings.mapped('partner_id').mapped('total_due_amount'))
        currency = request.env.company.currency_id
        overdue_amount_formatted = self._format_amount(overdue_amount, currency)

        return {
            'html': request.env.ref('freight_credit_control.freight_credit_dashboard_banner')._render({
                'blocked_count': blocked_count,
                'pending_count': pending_count,
                'ready_count': ready_count,
                'overdue_amount_formatted': overdue_amount_formatted,
            })
        }

    @staticmethod
    def _format_amount(amount, currency):
        decimals = currency.decimal_places if currency else 0
        formatted = '{:,.{prec}f}'.format(amount, prec=decimals)
        symbol = currency.symbol if currency else ''
        if currency and currency.position == 'after':
            return '%s %s' % (formatted, symbol)
        return '%s%s' % (symbol, formatted)
