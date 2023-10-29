from odoo import api, fields, models


class FreightLangSonBooking(models.Model):
    _inherit = "freight.booking"

    def _get_default_booking_type_for_langson(self):
        if self._context.get('branch_code') == 'LS':
            return "trading"
        return "forwarding"

    def _get_default_transport_type_for_langson(self):
        if self._context.get('branch_code') == 'LS':
            return "land"
        return "ocean"

    booking_type = fields.Selection(default=_get_default_booking_type_for_langson)
    transport_type = fields.Selection(default=_get_default_transport_type_for_langson)

    def _prepare_freight_booking_shptmt_number(self, values):
        if self._context.get('branch_code') == 'LS':
            seq = self.env["ir.sequence"]
            if "company_id" in values:
                seq = seq.with_company(values["company_id"])

            result = seq.next_by_code("freight.langson.booking.sequence") or "#"

            if result and result != "#":
                year = fields.Datetime.now().year
                result = result + "." + str(year)

                # Auto update booking number by shipment number when initial
                values['vessel_booking_number'] = result

            return result

        return super(FreightLangSonBooking, self)._prepare_freight_booking_shptmt_number(values)

    def _prepare_bill_values(self, booking):
        res = super(FreightLangSonBooking, self)._prepare_bill_values(booking)
        if self._context.get('branch_code') == 'LS' and res and booking:
            res['vessel_bol_number'] = booking.number
        return res
