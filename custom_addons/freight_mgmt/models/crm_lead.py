# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_send_lead_creation_notification(self, record):
        try:
            # Get the responsible salesperson (user) and record
            if record:
                salesperson = record.user_id
                partner_id = record.partner_id  # Customer/partner to whom the order is related
                created_user = record.create_uid
                lead_name = record.name
                contact = record.contact_name
                phone = record.phone

            if created_user and salesperson and created_user.id != salesperson.id:
                notification_ids = [((0, 0, {
                    'res_partner_id': salesperson.partner_id.id,
                    'notification_type': 'inbox'}))]
                channel = self.env['mail.channel'].channel_get([salesperson.partner_id.id])
                channel_id = self.env['mail.channel'].browse(channel["id"])
                lead_nam_link = ""
                if lead_name:
                    lead_nam_link = f"<a href='#id={record.id}&model=crm.lead'>{lead_name}</a>"
                message = _("A new lead has been created.<br>- Lead Name: <strong>%s</strong> <br>- Contact: %s <br>- Phone: %s" % (lead_nam_link, contact, phone))

                # Post an internal note to the chatter
                obj = channel_id.message_post(
                    body=(message),
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                    notification_ids=notification_ids,
                    partner_ids=[created_user.id],
                    notify_by_email=False,
                )

            # Send an email notification
            # template_name = "CRM: Lead Creation Notification Template"
            # email_template = self.env['mail.template'].search([('name', '=', template_name)], limit=1)
            email_template = self.env.ref("freight_mgmt.freight_crm_lead_creation_notification_template")
            if email_template:
                email_template.send_mail(record.id, force_send=False)

        except Exception as e:
            print("action_send_lead_creation_notification - Exception: " + str(e))

    @api.model
    def action_send_lead_follow_up_notification(self, record, days_passed):
        try:
            if not record:
                return False

            # Get the responsible salesperson (user) and record
            salesperson = record.user_id
            partner_id = record.partner_id  # Customer/partner to whom the order is related
            created_user = record.create_uid
            lead_name = record.name
            contact = record.contact_name
            phone = record.phone

            if created_user and salesperson and created_user.id != salesperson.id:
                notification_ids = [((0, 0, {
                    'res_partner_id': salesperson.partner_id.id,
                    'notification_type': 'inbox'}))]
                channel = self.env['mail.channel'].channel_get([salesperson.partner_id.id])
                channel_id = self.env['mail.channel'].browse(channel["id"])
                lead_nam_link = ""
                if lead_name:
                    lead_nam_link = f"<a href='#id={record.id}&model=crm.lead'>{lead_name}</a>"
                message = _(
                    "%s days have passed, have you followed up with this Lead yet?"
                    "<br>- Lead Name: <strong>%s</strong> <br>- Contact: %s <br>- Phone: %s"
                    % (days_passed, lead_nam_link, contact, phone))

                # Post an internal note to the chatter
                obj = channel_id.message_post(
                    body=(message),
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                    notification_ids=notification_ids,
                    partner_ids=[created_user.id],
                    notify_by_email=False,
                )

            # Send an email notification
            # template_name = "CRM: Lead Creation Notification Template"
            # email_template = self.env['mail.template'].search([('name', '=', template_name)], limit=1)
            email_template_id = f"freight_mgmt.freight_crm_lead_reminder_notification_template_{days_passed}_days"
            email_template = self.env.ref(email_template_id)
            if email_template:
                email_template.send_mail(record.id, force_send=False)

        except Exception as e:
            print("action_send_lead_follow_up_notification - Exception: " + str(e))
