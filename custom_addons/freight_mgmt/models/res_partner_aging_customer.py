# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class ResPartnerAgingCustomer(models.Model):
    _inherit = 'res.partner.aging.customer'

    def run_followup_reminder(self):
        overdue_records = self.search([
            ('total', '>', 0),
            '|', '|', '|', '|',
            ('days_due_01to30', '>', 0),
            ('days_due_31to60', '>', 0),
            ('days_due_61to90', '>', 0),
            ('days_due_91to120', '>', 0),
            ('days_due_121togr', '>', 0)
        ])

        template = self.env.ref('freight_mgmt.freight_email_template_debt_followup_reminder')

        for rec in overdue_records:
            template.send_mail(rec.id, force_send=False)

    def create_followup_activity(self):
        overdue_records = self.search([
            '|', '|', '|', '|',
            ('days_due_01to30', '>', 0),
            ('days_due_31to60', '>', 0),
            ('days_due_61to90', '>', 0),
            ('days_due_91to120', '>', 0),
            ('days_due_121togr', '>', 0)
        ])

        for rec in overdue_records:
            partner = rec.partner_id
            salesperson = partner.user_id

            if not salesperson or not partner:
                continue

            # summary = f'Debt Follow-up Required - B/L: {rec.bl_number}'
            summary_bl = f'Nhắc nợ quá hạn - B/L: {rec.bl_number}'
            summary_invoice = f'Nhắc nợ quá hạn - hóa đơn: {rec.invoice_ref}'
            summary = summary_bl
            if not rec.bl_number:
                summary = summary_invoice

            existing_activity = self.env['mail.activity'].sudo().search([
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', partner.id),
                ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
                ('summary', 'in', [summary_bl, summary_invoice]),
                ('date_deadline', '>=', fields.Date.today() - timedelta(days=7)),
            ], limit=1)

            if existing_activity:
                # note = f'⚠️Reminder: Customer {partner.name} still has overdue debt of invoice {rec.invoice_ref}. Please follow up urgently.'
                note = f'⚠️Nhắc lại: Khách hàng {partner.name} vẫn còn khoản nợ quá hạn - hóa đơn {rec.invoice_ref} - B/L: {rec.bl_number}. Vui lòng theo dõi và xử lý sớm.',

                # Cập nhật để Sales chú ý hơn
                existing_activity.write({
                    'note': note,
                    'priority': '3',
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                })
            else:
                # note = f'Customer {partner.name} has overdue debt of invoice #{rec.invoice_ref}. Please follow up.'
                note = f'Khách hàng {partner.name} đang có khoản nợ quá hạn - hóa đơn {rec.invoice_ref} - B/L: {rec.bl_number}. Vui lòng liên hệ và theo dõi để xử lý.'

                self.env['mail.activity'].create({
                    'res_model_id': self.env.ref('base.model_res_partner').id,
                    'res_id': partner.id,
                    'user_id': salesperson.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': summary,
                    'note': note,
                    'priority': '2',
                    'date_deadline': fields.Date.today(),
                })
