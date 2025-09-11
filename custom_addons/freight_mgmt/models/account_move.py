# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    vessel_bol_number = fields.Char(string="B/L Number", readonly=True, store=True)
    related_billing_id = fields.Many2one("freight.billing", string="B/L Number", readonly=True,
                                         compute="_compute_related_billing_id", store=False)

    @api.depends("vessel_bol_number")
    def _compute_related_billing_id(self):
        ''' This compute method makes a clickable link of vessel bol number in
        the accounting module to open the related billing within invoice form '''
        for rec in self:
            domain = [('vessel_bol_number', '=', rec.vessel_bol_number)]
            billing_id = self.env["freight.billing"].sudo().search(domain, limit=1)
            if billing_id:
                billing_id['display_name'] = rec.vessel_bol_number
                rec.related_billing_id = billing_id
            else:
                rec.related_billing_id = None

    @api.model
    def automate_action_set_bl_number_on_invoice_creation(self, record):
        try:
            if not record:
                return False

            sale_line_ids = record.invoice_line_ids.mapped('sale_line_ids')
            if sale_line_ids:
                sale_order = sale_line_ids[0].order_id
                if sale_order and sale_order.booking_id:
                    record.vessel_bol_number = sale_order.booking_id[0].vessel_bol_no
            else:
                purchase_order = record.invoice_line_ids.mapped('purchase_order_id')
                if purchase_order:
                    order_name = purchase_order[0].origin
                    sale_order = self.env['sale.order'].sudo().search([('name', '=', order_name)])
                    if sale_order and sale_order[0].booking_id:
                        record.vessel_bol_number = sale_order[0].booking_id[0].vessel_bol_no

            _logger.info("automate_action_set_bl_number_on_creation executed successful")
        except Exception as e:
            _logger.exception("automate_action_set_bl_number_on_creation - Exception: %s" % e)


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
                attachments = self.env['ir.attachment'].sudo().search([('res_id', '=', res_id), ('res_model', '=', res_model)])
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
