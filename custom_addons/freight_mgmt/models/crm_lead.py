# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from datetime import datetime, timedelta


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_generate_activities_on_lead_creation(self, record):
        """
        An automated action to send a private message in the Discuss chatter and an email to notify
        a lead has just been created or updated

        :param record: a crm lead record just created or updated
        """
        try:
            if not record:
                return False

            today = datetime.now()
            salesperson = record.user_id
            created_user = record.create_uid
            assigned_user_id = salesperson.id if salesperson else created_user.id
            notes = 'Báo cáo kết quả:'

            activity_types = self.env['mail.activity.type'].sudo().with_context(lang='en_US').search([('name', 'in', ['Need to do', 'Call', 'Meeting'])])
            for activity_type in activity_types:
                if activity_type.name == 'Need to do':
                    # To do - send quotation
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Chào giá - kết quả đạt được?',
                        note=notes,
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=5))
                    )
                elif activity_type.name == 'Call':
                    # Call 1 after 3 days
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Gọi lần 1 - kết quả đạt được?',
                        note=notes,
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=3))
                    )
                    # Call 2 after 10 days
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Gọi lần 2 - kết quả đạt được?',
                        note=notes,
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=10))
                    )
                    # Call 3 after 15 days
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Gọi lần 3 - kết quả đạt được?',
                        note=notes,
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=15))
                    )
                    # Call 4 after 30 days
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Gọi lần 4 - kết quả đạt được?',
                        note=notes,
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=30))
                    )
                    # Call 5 after 45 days
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Gọi lần 5 - kết quả đạt được?',
                        note=notes,
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=45))
                    )
                elif activity_type.name == 'Meeting':
                    record.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Cuộc họp - kết quả đạt được?',
                        user_id=assigned_user_id,
                        date_deadline=(today + timedelta(days=20))
                    )
        except Exception as e:
            print("action_generate_activities_on_lead_creation - Exception: " + str(e))

    @api.model
    def action_send_lead_creation_notification(self, record):
        """
        An automated action to send a private message in the Discuss chatter and an email to notify
        a lead has just been created or updated

        :param record: a crm lead record just created or updated
        """
        try:
            # Get the responsible salesperson (user) and record
            if record:
                salesperson = record.user_id
                created_user = record.create_uid
                lead_name = record.name
                contact = record.contact_name
                phone = record.phone

            if created_user and salesperson and created_user.id != salesperson.id:
                # Get the OdooBot user (id=1 is usually OdooBot)
                odoo_bot_author = self.env['res.users'].browse(1)
                channel = self.env['mail.channel'].channel_get([salesperson.partner_id.id])
                channel_id = self.env['mail.channel'].browse(channel["id"])
                lead_nam_link = ""
                if lead_name:
                    lead_nam_link = f"<a href='#id={record.id}&model=crm.lead'>{lead_name}</a>"
                message = _("A new lead has been created.<br>- Lead Name: <strong>%s</strong> <br>- "
                            "Contact: %s <br>- Phone: %s" % (lead_nam_link, contact, phone))

                # Send private message
                channel_id.message_post(
                    body=message,
                    author_id=odoo_bot_author.partner_id.id,
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                    notify_by_email=False
                )

            # Send an email notification
            email_template = self.env.ref("freight_mgmt.freight_crm_lead_creation_notification_template")
            if email_template:
                email_template.send_mail(record.id, force_send=False)

        except Exception as e:
            print("action_send_lead_creation_notification - Exception: " + str(e))

    @api.model
    def action_send_lead_follow_up_notification(self):
        """
        A scheduled action to send a private message in the Discuss chatter and an email to notify sales
        follow up with leads after N days
        """
        try:
            days_alert = [5, 10, 20, 30]

            now = datetime.now()
            domain = [
                ('active', '=', True),
                ('write_date', '>=', (now - timedelta(days=30)))  # Get records not older than 30 days
            ]
            records = self.env['crm.lead'].sudo().search(domain)
            for record in records:
                days_passed = (now - record.create_date).days
                if days_passed in days_alert:
                    self._send_notifications(record, days_passed)

        except Exception as e:
            print("action_send_lead_creation_notification - Exception: " + str(e))

    @api.model
    def action_auto_mark_lost_and_archive_leads(self):
        """
        A scheduled action to automate mark leads after 30 days as LOST and archive leads after 60 days
        without any activities
        """
        try:
            now = datetime.now()
            domain = [
                ('active', '=', True),
                ('type', '=', 'lead'),
                ('write_date', '<', (now - timedelta(days=60)))  # Get records older than 60 days
            ]
            records = self.env['crm.lead'].sudo().search(domain, limit=100)
            if records:
                records.write({'active': False})

            print("action_auto_mark_lost_and_archive_leads - executed successful.")

        except Exception as e:
            print("action_auto_mark_lost_and_archive_leads - Exception: " + str(e))

    def _send_notifications(self, record, days_passed):
        # Get the responsible salesperson (user) and record
        salesperson = record.user_id
        #partner_id = record.partner_id  # Customer/partner to whom the order is related
        created_user = record.create_uid
        lead_name = record.name
        contact = record.contact_name
        phone = record.phone

        if created_user and salesperson:
            # Create message to send in notification chat window
            lead_nam_link = ""
            if lead_name:
                lead_nam_link = f"<a href='#id={record.id}&model=crm.lead'>{lead_name}</a>"
            message = _(
                "%s days have passed, have you followed up with this Lead yet?"
                "<br>- Lead Name: <strong>%s</strong> <br>- Contact: %s <br>- Phone: %s"
                % (days_passed, lead_nam_link, contact, phone))

            # Get the OdooBot user (id=1 is usually OdooBot)
            odoo_bot_author = self.env['res.users'].browse(1)
            # notification_ids = [
            #     (0, 0, {
            #         'res_partner_id': salesperson.partner_id.id,
            #         'notification_type': 'inbox'
            #     }),
            #     (0, 0, {
            #         'res_partner_id': co_admin.partner_id.id,
            #         'notification_type': 'inbox'
            #     })
            # ]         # This is used to send group channel

            # Send notification to salesperson in the chatter
            channel = self.env['mail.channel'].channel_get([salesperson.partner_id.id])
            channel_id = self.env['mail.channel'].browse(channel["id"])

            # Send private message
            channel_id.message_post(
                body=message,
                author_id=odoo_bot_author.partner_id.id,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                notify_by_email=False
            )

            # # Post the message as a private message
            # self.env['mail.message'].create({
            #     'body': message,  # The message content
            #     'subject': 'Private Message',  # Optional subject
            #     'message_type': 'comment',  # Ensures it is a user message
            #     'subtype_id': self.env.ref('mail.mt_comment').id,  # Internal message subtype
            #     'partner_ids': [(4, salesperson.partner_id.id), (4, co_admin.partner_id.id)],  # The recipient(s)
            #     'author_id': self.env.user.partner_id.id,  # Sender's partner_id (current user)
            # })

        # Send an email notification
        # template_name = "CRM: Lead Creation Notification Template"
        # email_template = self.env['mail.template'].search([('name', '=', template_name)], limit=1)
        email_template_id = f"freight_mgmt.freight_crm_lead_reminder_notification_template_{days_passed}_days"
        email_template = self.env.ref(email_template_id)
        if email_template:
            email_template.send_mail(record.id, force_send=False)
