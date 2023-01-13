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

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        res = super(AccountMove, self).create(vals_list)

        try:
            '''
            Clone attachments from Debit/Credit Note to Invoice/Bill
            '''
            res_id = self.env.context.get("attachment_res_id")
            res_model = self.env.context.get("attachment_res_model")
            if res_id and res_model:
                new_attachments_list = []
                attachments = self.env['ir.attachment'].search([('res_id', '=', res_id), ('res_model', '=', res_model)])
                if attachments:
                    for att in attachments:
                        new_att = {
                            'res_model': 'account.move',
                            'res_id': res.id,
                            'name': att.name,
                            'company_id': att.company_id.id if att.company_id else False,
                            'type': att.type,
                            'url': att.url,
                            'mimetype': att.mimetype,
                            'store_fname': att.store_fname,
                            'file_size': att.file_size,
                            'checksum': att.checksum
                        }
                        new_attachments_list.append(new_att)

                    if new_attachments_list:
                        self.env['ir.attachment'].create(new_attachments_list)
        except:
            print("ERROR in OVERRIDE create method of account.move which trying clone attachments.")

        return res
