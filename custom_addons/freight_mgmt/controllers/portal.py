# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii
import pytz
from datetime import datetime

from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.tools import float_round
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager


class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        SaleOrder = request.env['sale.order']
        if 'quotation_count' in counters:
            values['quotation_count'] = SaleOrder.search_count(self._prepare_quotations_domain(partner)) \
                if SaleOrder.check_access_rights('read', raise_exception=False) else 0
        if 'order_count' in counters:
            values['order_count'] = SaleOrder.search_count(self._prepare_orders_domain(partner)) \
                if SaleOrder.check_access_rights('read', raise_exception=False) else 0

        return values

    def _prepare_quotations_domain(self, partner):
        return [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sent', 'cancel'])
        ]

    def _prepare_orders_domain(self, partner):
        return [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sale', 'done'])
        ]

    @http.route(['/my/notes', '/my/notes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = self._prepare_orders_domain(partner)

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager
        orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'order',
            'pager': pager,
            'default_url': '/my/orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("sale.portal_my_orders", values)

    @http.route(['/my/notes/<int:debit_id>'], type='http', auth="public", website=True)
    def portal_debit_note_page(self, debit_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            debit_sudo = self._document_check_access('freight.debit.note', debit_id, access_token=access_token)
            order_sudo = debit_sudo.order_id
            #order_id = order_sudo.id
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=debit_sudo, report_type=report_type,
                                     report_ref='freight_mgmt.freight_debit_note_report', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        if debit_sudo:
            # store the date as a string in the session to allow serialization
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_debit_%s' % debit_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_debit_%s' % debit_sudo.id] = now
                # body = _('Quotation viewed by customer %s', order_sudo.partner_id.name)
                # _message_post_helper(
                #     "sale.order",
                #     order_sudo.id,
                #     body,
                #     token=order_sudo.access_token,
                #     message_type="notification",
                #     subtype_xmlid="mail.mt_note",
                #     partner_ids=order_sudo.user_id.sudo().partner_id.ids,
                # )

        etd = ''
        etd_local = self._convert_utc_to_local(debit_sudo)
        if etd_local:
            etd = etd_local.strftime('%d-%B-%y')

        # volume = ""
        # if debit_sudo.booking_id.quantity > 0 and debit_sudo.booking_id.container_id.code:
        #     volume = "%sx%s" % (debit_sudo.booking_id.quantity, debit_sudo.booking_id.container_id.code)

        values = {
            'debit_sudo': debit_sudo,
            'sale_order': order_sudo,
            'partner_id': debit_sudo.partner_id,
            'partner_name': debit_sudo.partner_name,
            'partner_address': debit_sudo.partner_address,
            'partner_vat': debit_sudo.partner_vat,
            'bill_no': debit_sudo.bill_no,
            'pol': debit_sudo.pol,
            'pod': debit_sudo.pod,
            'etd': etd,
            'volume': debit_sudo.volume,
            'bank_name': debit_sudo.bank_name,
            'bank_acc_no': debit_sudo.bank_acc_no,
            'bank_acc_name': debit_sudo.bank_acc_name,
            'swift_code': debit_sudo.swift_code,
            'amount_total': debit_sudo.amount_total,
            'amount_subtotal_vnd': debit_sudo.amount_subtotal_vnd,
            'amount_vnd': debit_sudo.amount_total_vnd,
            'show_amount_total_vnd': debit_sudo.show_amount_total_vnd,
            'rate_date': debit_sudo.debit_date,
            'exchange_rate': debit_sudo.exchange_rate,
            #'vnd_currency': vnd,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'report_type': 'html',
            'action': debit_sudo._get_portal_return_action(),
        }
        if debit_sudo.company_id:
            values['res_company'] = debit_sudo.company_id

        # if order_sudo.state in ('draft', 'sent', 'cancel'):
        #     history = request.session.get('my_quotations_history', [])
        # else:
        #     history = request.session.get('my_orders_history', [])
        # values.update(get_records_pager(history, order_sudo))

        return request.render('freight_mgmt.debit_note_portal_template', values)

    def _convert_utc_to_local(self, debit_sudo):
        result = debit_sudo.etd
        if result:
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                utc_date_str = result.strftime(fmt)

                timezone = 'UTC'
                if debit_sudo.user_id.partner_id.tz:
                    timezone = debit_sudo.user_id.partner_id.tz
                tz = pytz.timezone(timezone)
                result = pytz.utc.localize(datetime.strptime(utc_date_str, fmt)).astimezone(tz)
            except:
                print("ERROR in _convert_utc_to_local")

            return result

