import datetime

from dateutil.relativedelta import *
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError


class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _order = "number desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin"]

    def _get_default_stage_id(self):
        return self.env["helpdesk.ticket.stage"].search([], limit=1).id

    def _get_default_description(self):
        description = self.env['ir.config_parameter'].sudo().get_param('helpdesk_mgmt.ticket_default_description', False)
        return description

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["helpdesk.ticket.stage"].search([])
        return stage_ids

    number = fields.Char(string="Ticket number", default="/", readonly=True, tracking=True)
    name = fields.Char(string="Title", required=True, tracking=True)
    description = fields.Html(required=True, sanitize_style=True, default=_get_default_description)
    user_id = fields.Many2one(
        comodel_name="res.users", string="Assigned user", tracking=True, index=True
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        default=_get_default_stage_id,
        tracking=True,
        ondelete="restrict",
        index=True,
        copy=False,
    )
    processing_day = fields.Integer(related="stage_id.processing_day", readonly=True, store=False)
    is_processing_time_warning = fields.Boolean(compute="_compute_is_processing_time_warning", store=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact", tracking=True)
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email", tracking=True)

    is_last_month_search = fields.Boolean(compute="_compute_is_last_month_search",
                                          search="_search_is_last_month_search")
    is_this_month_search = fields.Boolean(compute="_compute_is_this_month_search",
                                          search="_search_is_this_month_search")
    is_last_three_month_search = fields.Boolean(compute="_compute_is_last_three_month_search",
                                                search="_search_is_last_three_month_search")
    is_last_quarter_search = fields.Boolean(compute="_compute_is_last_quarter_search",
                                            search="_search_is_last_quarter_search")
    is_this_quarter_search = fields.Boolean(compute="_compute_is_this_quarter_search",
                                            search="_search_is_this_quarter_search")

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    assigned_date = fields.Datetime()
    closed_date = fields.Datetime()
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Tags", tracking=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
        help="Channel indicates where the source of a ticket"
        "comes from (it could be a phone call, an email...)",
        tracking=True
    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
        tracking = True
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team",
        tracking=True
    )
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        default="1",
        tracking=True
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket")],
        string="Media Attachments",
    )
    color = fields.Integer(string="Color Index", compute="_get_color")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
    )
    active = fields.Boolean(default=True, tracking=True)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    def action_schedule_processing_time_warning(self):
        try:
            print("action_schedule_processing_time_warning is called.")
            unclosed_tickets = self.search([('processing_day', '>', 0), ('stage_id.closed', '!=', True)])
            if unclosed_tickets:
                now = fields.Datetime.now()
                for rec in unclosed_tickets:
                    if rec.processing_day > 0 and rec.last_stage_update:
                        warning_time = rec.last_stage_update + datetime.timedelta(days=rec.processing_day)
                        if now > warning_time:
                            rec.is_processing_time_warning = True

            print("action_schedule_processing_time_warning was done")
        except Exception as e:
            print("action_schedule_processing_time_warning error: " + str(e))

    def _compute_is_last_month_search(self):
        for rec in self:
            rec.is_last_month_search = False

    def _compute_is_this_month_search(self):
        for rec in self:
            rec.is_this_month_search = False

    def _compute_is_last_three_month_search(self):
        for rec in self:
            rec.is_last_three_month_search = False

    def _compute_is_last_quarter_search(self):
        for rec in self:
            rec.is_last_quarter_search = False

    def _compute_is_this_quarter_search(self):
        for rec in self:
            rec.is_this_quarter_search = False

    def _search_is_last_month_search(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        now = fields.Datetime.now()
        previous_month = now - relativedelta(months=1)
        from_date = datetime.datetime(previous_month.year, previous_month.month, 1)
        to_date = from_date + relativedelta(months=1)
        tickets = self.env['helpdesk.ticket'].search([('create_date', '>=', from_date), ('create_date', '<', to_date)])
        return [('id', 'in', tickets.ids)]

    def _search_is_this_month_search(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        now = fields.Datetime.now()
        from_date = datetime.datetime(now.year, now.month, 1)
        tickets = self.env['helpdesk.ticket'].search([('create_date', '>=', from_date)])
        return [('id', 'in', tickets.ids)]

    def _search_is_last_three_month_search(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        now = fields.Datetime.now()
        previous_3_months = now - relativedelta(months=3)
        from_date = datetime.datetime(previous_3_months.year, previous_3_months.month, 1)
        to_date = from_date + relativedelta(months=3)
        tickets = self.env['helpdesk.ticket'].search([('create_date', '>=', from_date), ('create_date', '<', to_date)])
        return [('id', 'in', tickets.ids)]

    def _search_is_last_quarter_search(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        now = fields.Datetime.now()
        previous_3_months = now - relativedelta(months=3)
        last_quarter = int((previous_3_months.month - 1) / 3 + 1)
        from_date = datetime.datetime(previous_3_months.year, 3 * last_quarter - 2, 1)
        to_date = from_date + relativedelta(months=3)
        tickets = self.env['helpdesk.ticket'].search([('create_date', '>=', from_date), ('create_date', '<', to_date)])
        return [('id', 'in', tickets.ids)]

    def _search_is_this_quarter_search(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        now = fields.Datetime.now()
        this_quarter = int((now.month - 1) / 3 + 1)
        from_date = datetime.datetime(now.year, 3 * this_quarter - 2, 1)
        to_date = from_date + relativedelta(months=3)
        tickets = self.env['helpdesk.ticket'].search([('create_date', '>=', from_date), ('create_date', '<', to_date)])
        return [('id', 'in', tickets.ids)]

    @api.depends("processing_day", "last_stage_update")
    def _compute_is_processing_time_warning(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_processing_time_warning = False
            if rec.processing_day > 0 and rec.last_stage_update:
                warning_time = rec.last_stage_update + datetime.timedelta(days=rec.processing_day)
                if now > warning_time:
                    rec.is_processing_time_warning = True

    @api.depends("is_processing_time_warning")
    def _get_color(self):
        """Compute Color value according to the conditions"""
        for rec in self:
            if rec.is_processing_time_warning:
                rec.color = 1   # Red
            else:
                rec.color = 0   # Gray

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    @api.onchange("team_id", "user_id")
    def _onchange_dominion_user_id(self):
        if self.user_id and self.user_ids and self.user_id not in self.team_id.user_ids:
            self.update({"user_id": False})
            return {"domain": {"user_id": []}}
        if self.team_id:
            return {"domain": {"user_id": [("id", "in", self.user_ids.ids)]}}
        else:
            return {"domain": {"user_id": []}}

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        now = fields.Datetime.now()
        if vals.get("number", "/") == "/":
            vals["number"] = self._prepare_ticket_number(vals)
        if vals.get("user_id"):
            vals["assigned_date"] = now
        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.closed:
                    vals["closed_date"] = now
            if vals.get("user_id"):
                vals["assigned_date"] = now
        return super().write(vals)

    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        # ticket = self[0]
        # if "stage_id" in tracking and ticket.stage_id.mail_template_id:
        #     res["stage_id"] = (
        #         ticket.stage_id.mail_template_id,
        #         {
        #             "auto_delete_message": True,
        #             "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
        #                 "mail.mt_note"
        #             ),
        #             "email_layout_xmlid": "mail.mail_notification_light",
        #         },
        #     )
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        ticket = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)

        return ticket

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(partner_ids)
        return super().message_update(msg, update_vals=update_vals)

    # def _message_post_after_hook(self, message, msg_vals):
    #     res = super(HelpdeskTicket, self)._message_post_after_hook(message, msg_vals)
    #     for this in self:
    #         for follower in this.message_follower_ids:
    #             follower.unlink()
    #     return res

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id:
                    ticket._message_add_suggested_recipient(
                        recipients, partner=ticket.partner_id, reason=_("Customer")
                    )
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(
                        recipients,
                        email=ticket.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients
