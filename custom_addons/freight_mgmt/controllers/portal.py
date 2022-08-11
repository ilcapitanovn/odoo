# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii

from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.portal.controllers.mail import _message_post_helper
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

    @http.route(['/my/notes/<int:billing_id>'], type='http', auth="public", website=True)
    def portal_billing_page(self, billing_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            billing_sudo = self._document_check_access('freight.billing', billing_id, access_token=access_token)
            order_sudo = billing_sudo.order_id
            order_id = order_sudo.id
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=billing_sudo, report_type=report_type, report_ref='freight_mgmt.freight_debit_note_report', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        if order_sudo:
            # store the date as a string in the session to allow serialization
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_quote_%s' % order_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_quote_%s' % order_sudo.id] = now
                #body = _('Quotation viewed by customer %s', order_sudo.partner_id.name)
                # _message_post_helper(
                #     "sale.order",
                #     order_sudo.id,
                #     body,
                #     token=order_sudo.access_token,
                #     message_type="notification",
                #     subtype_xmlid="mail.mt_note",
                #     partner_ids=order_sudo.user_id.sudo().partner_id.ids,
                # )

        usd = request.env['res.currency'].search([('name', '=', 'USD')])
        vnd = request.env['res.currency'].search([('name', '=', 'VND')])
        company = order_sudo.company_id
        now = fields.Datetime.now()
        amount_vnd = usd._convert(order_sudo.amount_total, vnd, company, now)
        rate_date = vnd.date
        exchange_rate = vnd.rate

        etd = ''
        if billing_sudo.booking_id.etd_revised:
            etd = billing_sudo.booking_id.etd_revised.strftime('%d-%B-%y')

        volume = ""
        if billing_sudo.booking_id.quantity > 0 and billing_sudo.booking_id.container_id.code:
            volume = "%sx%s" % (billing_sudo.booking_id.quantity, billing_sudo.booking_id.container_id.code)

        bank_name = ""
        bank_acc_no = ""
        bank_acc_name = ""
        swift_code = ""
        for bnk in billing_sudo.company_id.bank_ids:
            if not bank_name:
                bank_name = bnk.bank_name
                bank_acc_no = bnk.acc_number
                bank_acc_name = bnk.acc_holder_name
                swift_code = bnk.bank_bic

        values = {
            'billing_sudo': billing_sudo,
            'sale_order': order_sudo,
            'partner_id': order_sudo.partner_id.id,
            'partner_name': order_sudo.partner_id.display_name,
            'partner_address': order_sudo.partner_id.contact_address,
            'bill_no': billing_sudo.vessel_bol_number,
            'pol': billing_sudo.port_loading_id.name,
            'pod': billing_sudo.port_discharge_id.name,
            'etd': etd,
            'volume': volume,
            'bank_name': bank_name,
            'bank_acc_no': bank_acc_no,
            'bank_acc_name': bank_acc_name,
            'swift_code': swift_code,
            'amount_vnd': amount_vnd,
            'rate_date': rate_date,
            'exchange_rate': exchange_rate,
            'vnd_currency': vnd,
            'message': message,
            'token': access_token,
            'landing_route': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': billing_sudo._get_portal_return_action(),
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        # Payment values
        # if order_sudo.has_to_be_paid():
        #     logged_in = not request.env.user._is_public()
        #     acquirers_sudo = request.env['payment.acquirer'].sudo()._get_compatible_acquirers(
        #         order_sudo.company_id.id,
        #         order_sudo.partner_id.id,
        #         currency_id=order_sudo.currency_id.id,
        #         sale_order_id=order_sudo.id,
        #     )  # In sudo mode to read the fields of acquirers and partner (if not logged in)
        #     tokens = request.env['payment.token'].search([
        #         ('acquirer_id', 'in', acquirers_sudo.ids),
        #         ('partner_id', '=', order_sudo.partner_id.id)
        #     ]) if logged_in else request.env['payment.token']
        #     fees_by_acquirer = {
        #         acquirer: acquirer._compute_fees(
        #             order_sudo.amount_total,
        #             order_sudo.currency_id,
        #             order_sudo.partner_id.country_id,
        #         ) for acquirer in acquirers_sudo.filtered('fees_active')
        #     }
        #     # Prevent public partner from saving payment methods but force it for logged in partners
        #     # buying subscription products
        #     show_tokenize_input = logged_in \
        #         and not request.env['payment.acquirer'].sudo()._is_tokenization_required(
        #             sale_order_id=order_sudo.id
        #         )
        #
        #     values.update({
        #         'acquirers': acquirers_sudo,
        #         'tokens': tokens,
        #         'fees_by_acquirer': fees_by_acquirer,
        #         'show_tokenize_input': show_tokenize_input,
        #         'amount': order_sudo.amount_total,
        #         'currency': order_sudo.pricelist_id.currency_id,
        #         'access_token': order_sudo.access_token,
        #         'transaction_route': order_sudo.get_portal_url(suffix='/transaction'),
        #         'landing_route': order_sudo.get_portal_url(),
        #     })

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        return request.render('freight_mgmt.debit_note_portal_template', values)

