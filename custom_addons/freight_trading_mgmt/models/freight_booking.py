from odoo import api, fields, models


class FreightTradingBooking(models.Model):
    _inherit = "freight.booking"

    def _get_default_booking_type_for_trading(self):
        if self._context.get('branch_code') == 'TRA':
            return "trading"
        return "forwarding"

    def _get_default_transport_type_for_trading(self):
        if self._context.get('branch_code') == 'TRA':
            return "land"
        return "ocean"

    booking_type = fields.Selection(default=_get_default_booking_type_for_trading)
    transport_type = fields.Selection(default=_get_default_transport_type_for_trading)

    def _prepare_freight_booking_shptmt_number(self, values):
        if self._context.get('branch_code') == 'TRA':
            seq = self.env["ir.sequence"]
            if "company_id" in values:
                seq = seq.with_company(values["company_id"])

            seq_date = None
            if 'etd_revised' in values and values['etd_revised']:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['etd_revised']))

            result = seq.next_by_code("freight.trading.booking.sequence", sequence_date=seq_date) or "#"

            if result and result != "#":
                """ Update sequence month prefix if the month of the revised ETD is difference the current month
                Because automated sequence is always returned current month
                """
                if seq_date:
                    now = fields.Datetime.context_timestamp(self, fields.Datetime.now())  # now in local time zone
                    if seq_date.month != now.month:
                        new_seq = result.split('-')
                        if new_seq and len(new_seq) > 1:
                            seq_next = new_seq[1]
                            seq_prefix_new = seq_date.strftime('TRA%m%y-')
                            result = seq_prefix_new + seq_next

                # Auto update booking number by shipment number when initial
                values['vessel_booking_number'] = result

            return result

        return super(FreightTradingBooking, self)._prepare_freight_booking_shptmt_number(values)

    def _prepare_bill_values(self, booking):
        res = super(FreightTradingBooking, self)._prepare_bill_values(booking)
        if self._context.get('branch_code') == 'TRA' and res and booking:
            res['vessel_bol_number'] = booking.number
        return res
