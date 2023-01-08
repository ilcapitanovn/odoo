# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    vessel_bol_number = fields.Char(compute="_compute_vessel_bol_number", string="B/L Number", readonly=True, store=False)

    def _compute_vessel_bol_number(self):
        for rec in self:
            rec.vessel_bol_number = ''
            sale_line_ids = rec.invoice_line_ids.mapped('sale_line_ids')
            if sale_line_ids:
                sale_order = sale_line_ids[0].order_id
                if sale_order and sale_order.booking_id:
                    rec.vessel_bol_number = sale_order.booking_id[0].vessel_bol_no
            else:
                purchase_order = rec.invoice_line_ids.mapped('purchase_order_id')
                if purchase_order:
                    order_name = purchase_order[0].origin
                    sale_order = self.env['sale.order'].search([('name', '=', order_name)])
                    if sale_order and sale_order[0].booking_id:
                        rec.vessel_bol_number = sale_order[0].booking_id[0].vessel_bol_no

