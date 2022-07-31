from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError


class FreightBooking(models.Model):
    _name = "freight.booking"
    _description = "Freight Booking"
    _rec_name = "number"
    _order = "number desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin"]

    def _get_default_stage_id(self):
        return self.env["freight.catalog.stage"].search([], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["freight.catalog.stage"].search([])
        return stage_ids

    number = fields.Char(string="SHPTMT Number", default="#", readonly=True, required=True)
    name = fields.Char(string="Title")
    description = fields.Char(translate=True)

    vessel_booking_number = fields.Char(string="Booking Number")
    vessel_bol_number = fields.Char(string="B/L Number")

    parent_id = fields.Many2one('freight.booking', string='Parent Booking', index=True)
    child_ids = fields.One2many('freight.booking', 'parent_id', string="Sub-bookings")

    billing_id = fields.One2many('freight.billing', 'booking_id', string='Bill Reference', auto_join=True)

    partner_id = fields.Many2one(comodel_name="res.partner",
                                 string="Customer", readonly=True)
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")

    transport_type = fields.Selection(
        selection=[("ocean", "Ocean"), ("air", "Air"), ("express", "Express")],
        string="Transport Type", default="ocean", help='Type of Transport')

    shipment_type = fields.Selection(
        selection=[("fcl-exp", "FCL Export"), ("fcl-imp", "FCL Import"), ("lcl-exp", "LCL Export"),
                   ("lcl-imp", "LCL Import"), ("air-imp", "Air Import"), ("air-exp", "Air Export")],
        string="Shipment Type", default="fcl-exp", help='Type of Shipment')

    order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order Reference",
        domain="['|', ('invoice_status','=','to invoice'), ('invoice_status','=','invoiced')]",
        tracking=True, index=True
    )
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    margin = fields.Monetary(related="order_id.margin", string="Profit",
                             currency_field="currency_id", readonly=True, store=False)

    booking_type = fields.Selection([
        ('forwarding', 'Forwarding'),
        ('trading', 'Trading'),
    ], string='Booking Type', default='forwarding', required=True, tracking=True)

    container_id = fields.Many2one(
        comodel_name="freight.catalog.container", string="Container", tracking=True, index=True
    )
    stage_id = fields.Many2one(
        comodel_name="freight.catalog.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        default=_get_default_stage_id,
        tracking=True,
        ondelete="restrict",
        index=True,
        copy=False,
    )
    user_id = fields.Many2one(
        comodel_name="res.users", string="Assigned user", tracking=True, index=True
    )
    port_loading_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Loading Port", tracking=True, index=True
    )
    port_discharge_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Discharge Port", tracking=True, index=True
    )
    place_of_delivery = fields.Char(string="Destination")
    vessel_id = fields.Many2one(
        comodel_name="freight.catalog.vessel", string="Vessel", tracking=True, index=True
    )
    shipping_line = fields.Char(string="Shipping Line")
    ro = fields.Char(string="R.O.")
    commodity = fields.Char(string="Commodity")
    quantity = fields.Integer(string="Quantity")
    temperature = fields.Char(string="Temperature (C)")
    ventilation = fields.Char(string="Ventilation (CBM/H)")
    voyage_number = fields.Char(string="Voyage No.")
    gross_weight = fields.Float(string='Gross Weight (KGS)')
    etd = fields.Datetime(string="Original ETD", store=True)
    etd_revised = fields.Datetime(string="Revised ETD", store=True)
    eta = fields.Datetime(string="Est. Time Arrival", store=True)

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    closing_time = fields.Datetime(string="SI Cut Off Time", store=True)
    issued_date = fields.Datetime(string="Issued Date", store=True)
    approved_date = fields.Datetime(string="Confirmed Date", store=True)
    completed_date = fields.Datetime(string="Completed Date", store=True)
    completed = fields.Boolean(related="stage_id.completed")

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked")
        ],
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self:
            # res.append((rec.id, rec.number + " - " + rec.name))
            res.append((rec.id, rec.number))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    def create_bill_lading(self):
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = self.id

        #bookings = self.env['freight.booking'].browse(active_ids)

        #new_bills = self._create_bills()

            # 1) Create bookings.
            bill_vals_list = []
            for booking in self:
                # booking = booking.with_company(booking.company_id)
                bill_vals = self._prepare_bill_values(booking)

                bill_vals_list.append(bill_vals)

            if not bill_vals_list:
                raise self._nothing_to_invoice_error()

            new_bills = self.env['freight.billing'].sudo().with_context().create(bill_vals_list)

            if new_bills:
                # for order in sale_orders:
                #     order.booking_status = 'booked'

                return self._open_view_billing(new_bills)

    def _open_view_billing(self, new_bills):
        billing_form = self.env.ref('freight_mgmt.freight_billing_view_form', False)

        if isinstance(new_bills.ids, list):
            new_bill_id = new_bills.ids[0]
        else:
            new_bill_id = new_bills.id

        if billing_form and new_bill_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'freight.billing',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'views': [(billing_form.id, 'form')],
                'view_id': billing_form.id,
                'res_id': new_bill_id,
            }

    def _prepare_bill_values(self, booking):
        bill_vals = {
            'booking_id': booking.id,
            'port_loading_id': booking.port_loading_id.id,
            'port_discharge_id': booking.port_discharge_id.id,
            'port_loading_id': booking.port_loading_id.id,
            'vessel_id': booking.vessel_id.id,
            'order_id': booking.order_id.id,
            'user_id': booking.order_id.user_id.id,
            'partner_id': booking.partner_id.id,
        }

        return bill_vals

    @api.model
    def _nothing_to_invoice_error(self):
        return UserError(_(
            "There is nothing to booking!\n\n"
            "Reason(s) of this behavior could be:\n"
            "- You should invoice your orders before booking them: Click on the \"truck\" icon "
            "(top-right of your screen) and follow instructions.\n"
            "- You should modify the booking policy of your order: Open the Freight, go to the "
            "\"Configuration\" tab and modify booking policy from \"Orders\" to \"Invoiced\"."
            " For Services, you should modify the Service Booking Policy to "
            "'Prepaid'."
        ))

    @api.onchange("order_id")
    def _onchange_order_id(self):
        if self.order_id:
            self.user_id = self.order_id.user_id
            self.partner_id = self.order_id.partner_id

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    # @api.onchange("user_id")
    # def _onchange_dominion_user_id(self):
    #     if self.user_id: # and self.user_ids:
    #         self.update({"user_id": False})
    #         return {"domain": {"user_id": []}}
    #     # if self.team_id:
    #     #     return {"domain": {"user_id": [("id", "in", self.user_ids.ids)]}}
    #     else:
    #         return {"domain": {"user_id": []}}

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("number", "#") == "#":
            vals["number"] = self._prepare_freight_booking_shptmt_number(vals)
        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_freight_booking_shptmt_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["freight.catalog.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.completed:
                    vals["completed_date"] = now
            if vals.get("user_id"):
                vals["issued_date"] = now
        return super().write(vals)

    def action_duplicate_freight_booking(self):
        for booking in self.browse(self.env.context["active_ids"]):
            booking.copy()

    def _prepare_freight_booking_shptmt_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("freight.booking.sequence") or "#"

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        # freight_booking = self[0]
        # if "stage_id" in tracking and freight_booking.stage_id.mail_template_id:
        #     res["stage_id"] = (
        #         freight_booking.stage_id.mail_template_id,
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
        freight_booking = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=freight_booking, force_create=False
            )
            if p
        ]
        freight_booking.message_subscribe(partner_ids)

        return freight_booking

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

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for booking in self:
                if booking.partner_id:
                    booking._message_add_suggested_recipient(
                        recipients, partner=booking.partner_id, reason=_("Customer")
                    )
                elif booking.partner_email:
                    booking._message_add_suggested_recipient(
                        recipients,
                        email=booking.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients
