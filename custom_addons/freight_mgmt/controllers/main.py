import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FreightBookingController(http.Controller):
    @http.route("/booking/close", type="http", auth="user")
    def support_booking_close(self, **kw):
        """Close the support booking"""
        values = {}
        for field_name, field_value in kw.items():
            if field_name.endswith("_id"):
                values[field_name] = int(field_value)
            else:
                values[field_name] = field_value
        booking = (
            http.request.env["freight.booking"]
            .sudo()
            .search([("id", "=", values["booking_id"])])
        )
        booking.stage_id = values.get("stage_id")

        return werkzeug.utils.redirect("/my/booking/" + str(booking.id))

    @http.route("/freight/booking/get_url", type="json", auth="user", methods=['POST'], csrf=False)
    def get_booking_list_url(self, **kw):
        url = request.env['ir.config_parameter'].sudo().get_param('open_booking_list_url', False)
        return {
            'booking_url': url
        }
