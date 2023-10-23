from odoo import fields, models


class FreightLangSonBooking(models.Model):
    _inherit = "freight.booking"

    def _prepare_freight_booking_shptmt_number(self, values):
        if self._context.get('branch_code') == 'LS':
            seq = self.env["ir.sequence"]
            if "company_id" in values:
                seq = seq.with_company(values["company_id"])

            result = seq.next_by_code("freight.langson.booking.sequence") or "#"

            if result and result != "#":
                year = fields.Datetime.now().year
                result = result + "." + str(year)

            return result

        return super(FreightLangSonBooking, self)._prepare_freight_booking_shptmt_number(values)
