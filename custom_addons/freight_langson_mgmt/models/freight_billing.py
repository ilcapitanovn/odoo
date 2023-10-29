from odoo import api, fields, models


class FreightLangSonBilling(models.Model):
    _inherit = "freight.billing"

    transport_route = fields.Char(related="booking_id.transport_route", store=True, readonly=False, tracking=True)
    transport_type = fields.Selection(related="booking_id.transport_type", store=False, readonly=True)
    issued_date = fields.Datetime(related="booking_id.issued_date", store=False, readonly=True)
    etd_revised = fields.Datetime(related="booking_id.etd_revised", store=False, readonly=True)

    print_report_type = fields.Selection(
        selection=[("rp1", "Regular B/L"), ("rp2", "International B/L")],
        string="Print Report", default="rp1", help='Type of Print BL Report')

    @api.onchange("booking_id")
    def _onchange_booking_id(self):
        if self._context.get('branch_code') == 'LS' and self.booking_id:
            self.vessel_bol_number = self.booking_id.number
