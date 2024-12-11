from datetime import timedelta
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError, ValidationError


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

    number = fields.Char(string="SHPTMT Number", default="#", tracking=True, required=True)
    name = fields.Char(string="Title")
    description = fields.Char(translate=True)

    vessel_booking_number = fields.Char(string="Booking Number")

    parent_id = fields.Many2one('freight.booking', string='Parent Booking', index=True)
    child_ids = fields.One2many('freight.booking', 'parent_id', string="Sub-bookings")

    billing_id = fields.One2many('freight.billing', 'booking_id', string='Bill Reference', auto_join=True)
    billing_count = fields.Integer(
        "Number of BL",
        compute='_compute_billing_count')
    vessel_bol_no = fields.Char(string="B/L Number", related="billing_id.vessel_bol_number", readonly=True)

    partner_id = fields.Many2one(comodel_name="res.partner",
                                 string="Customer", tracking=True)
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")

    transport_route = fields.Char(string="Transport Route")
    transport_type = fields.Selection(
        selection=[("ocean", "Ocean"), ("land", "Land"), ("air", "Air"), ("express", "Express")],
        string="Transport Type", default="ocean", help='Type of Transport')

    # shipment_type = fields.Selection(
    #     selection=[("fcl-exp", "FCL Export"), ("fcl-imp", "FCL Import"), ("lcl-exp", "LCL Export"),
    #                ("lcl-imp", "LCL Import"), ("air-imp", "Air Import"), ("air-exp", "Air Export")],
    #     string="Shipment Type", default="fcl-exp", help='Type of Shipment')
    shipment_type = fields.Selection(related="order_id.order_shipment_type", string="Shipment Type", store=True,
                                     readonly=True, help='Type of Shipment')

    order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order Reference",
        #domain="['|', ('invoice_status','=','to invoice'), ('invoice_status','=','invoiced')]",
        domain=lambda self: self._get_order_id_domain(),
        tracking=True, index=True
    )
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    amount_total = fields.Monetary(related="order_id.amount_total", string="Total",
                                   currency_field="currency_id", readonly=True, store=True)
    margin = fields.Monetary(related="order_id.margin", string="Profit",
                             currency_field="currency_id", readonly=True, store=True)

    booking_type = fields.Selection([
        ('forwarding', 'Forwarding'),
        ('trading', 'Trading'),
    ], string='Booking Type', default='forwarding', required=True, tracking=True)

    # order_type = fields.Selection([
    #     ('freehand', 'Freehand'),
    #     ('nominated', 'Nominated'),
    # ], string='Order Type')
    order_type = fields.Selection(related="order_id.order_type", string="Order Type", store=True, readonly=True)

    booking_volumes = fields.One2many('freight.booking.volume', 'booking_id', string="Booking volumes")
    volumes_display = fields.Char(compute="_compute_volumes_display", string="Volumes", store=False)

    # TODO: Should delete this field since it's replaced by o2m booking_volumes
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
    port_stopover_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Stopover Port", tracking=True, index=True
    )
    place_of_delivery = fields.Char(string="Destination", tracking=True)
    vessel_id = fields.Many2one(
        comodel_name="freight.catalog.vessel", string="Line", tracking=True, index=True
    )
    vehicle_supplier_id = fields.Many2one(
        comodel_name="freight.catalog.vehicle.supplier", string="Vehicle Supplier", tracking=True, index=True
    )
    vehicle_number = fields.Char(string="Car Number", tracking=True)
    shipping_line = fields.Char(string="Shipping Line", tracking=True)     # TODO: Possible duplicate with vessel_id, need to check
    ro = fields.Char(string="R.O.", tracking=True)
    commodity = fields.Char(string="Commodity", tracking=True)
    quantity = fields.Integer(string="Quantity", tracking=True)    # TODO: Should delete this field since it's replaced by o2m
    temperature = fields.Char(string="Temperature (C)", tracking=True)
    ventilation = fields.Char(string="Ventilation (CBM/H)", tracking=True)
    voyage_number = fields.Char(string="Voyage No.", tracking=True)
    gross_weight = fields.Float(string='Gross Weight (KGS)', tracking=True)
    etd = fields.Datetime(string="Original ETD", tracking=True, store=True)
    etd_revised = fields.Datetime(string="Revised ETD", tracking=True, store=True)
    eta = fields.Datetime(string="Est. Time Arrival", tracking=True, store=True)

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    closing_time = fields.Datetime(string="SI Cut Off Time", tracking=True, store=True)
    issued_date = fields.Datetime(string="Issued Date", tracking=True, store=True)
    approved_date = fields.Datetime(string="Confirmed Date", tracking=True, store=True)
    completed_date = fields.Datetime(string="Completed Date", tracking=True, store=True)
    confirmed = fields.Boolean(related="stage_id.confirmed")
    completed = fields.Boolean(related="stage_id.completed")
    stage_name = fields.Char(related="stage_id.name", readonly=True, store=False)

    arrival_notice_count = fields.Integer(string="Arrival Notice Count", tracking=True, default=1)
    demurrage_time = fields.Datetime(string="Demurrage (DEM)", tracking=True)   # Deprecated, consider to delete
    demurrage_days = fields.Integer(string="Demurrage (DEM)", tracking=True, default=7)
    detention_days = fields.Integer(string="Detention (DET)", tracking=True, default=7)
    storage_days = fields.Integer(string="Storage", tracking=True, default=7)
    storage_time = fields.Datetime(string="Storage Time", tracking=True)   # Deprecated, consider to delete

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    branch_id = fields.Many2one(related="order_id.branch_id", string='Branch', store=True)

    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked")
        ],
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [('uniq_booking_number', 'unique(number)',
                         'A booking number already exists with this name. Please choose another one!')]

    def name_get(self):
        res = []
        for rec in self:
            # res.append((rec.id, rec.number + " - " + rec.name))
            res.append((rec.id, rec.number))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    def action_confirm(self):
        if not self.vessel_booking_number:
            raise UserError(_("A Booking Number is required in order to confirm the booking."))

        stage = self.env["freight.catalog.stage"].search([('confirmed', '=', True)], limit=1)
        if stage and stage.id:
            self.write({'stage_id': stage.id})

    def action_view_billing(self):
        if not self.billing_id:
            raise UserError(_("The selected booking and its related bill is invalid to view."))

        action = self._open_view_billing(self.billing_id)
        return action

    def create_bill_lading(self):
        # 1) Create bills.
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
        port_loading_text = ''
        port_discharge_text = ''

        if booking.port_loading_id:
            port_loading_text = booking.port_loading_id.name
            if booking.port_loading_id.country_id:
                port_loading_text += ', ' + booking.port_loading_id.country_id.name

        if booking.port_discharge_id:
            port_discharge_text = booking.port_discharge_id.name
            if booking.port_discharge_id.country_id:
                port_discharge_text += ', ' + booking.port_discharge_id.country_id.name

        bill_vals = {
            'booking_id': booking.id,
            # 'port_loading_id': booking.port_loading_id.id,
            # 'port_discharge_id': booking.port_discharge_id.id,
            # 'port_loading_id': booking.port_loading_id.id,
            # 'vessel_id': booking.vessel_id.id,
            'order_id': booking.order_id.id,
            'user_id': booking.order_id.user_id.id,
            'partner_id': booking.partner_id.id,
            'port_loading_text': port_loading_text,
            'port_discharge_text': port_discharge_text,
        }

        return bill_vals

    @api.depends('billing_id')
    def _compute_billing_count(self):
        for rec in self:
            rec.billing_count = len(rec.billing_id)

    @api.depends('billing_id')
    def _compute_vessel_bol_number(self):
        for rec in self:
            if rec.billing_id:
                rec.vessel_bol_number = rec.billing_id.vessel_bol_number

    @api.depends('booking_volumes')
    def _compute_volumes_display(self):
        for rec in self:
            if rec.booking_volumes:
                for item in rec.booking_volumes:
                    if item.container_id:
                        if rec.volumes_display:
                            rec.volumes_display += ', %sx%s' % (item.quantity, item.container_id.code)
                        else:
                            rec.volumes_display = '%sx%s' % (item.quantity, item.container_id.code)
                    else:
                        rec.volumes_display = ''
            else:
                rec.volumes_display = ''

    @api.model
    def default_get(self, fields_list):
        res = super(FreightBooking, self).default_get(fields_list)
        res.update({
            'order_type': 'freehand' or False
        })
        return res

    @api.model
    def _get_order_id_domain(self):
        if self.env.context.get("shipment_type_suffix") == 'imp':
            res = ['&', ('order_shipment_type', 'in', ('fcl-imp', 'lcl-imp', 'air-imp')),
                   '|', ('invoice_status', '=', 'to invoice'), ('invoice_status', '=', 'invoiced')]
        else:
            res = ['&', ('order_shipment_type', 'not in', ('fcl-imp', 'lcl-imp', 'air-imp')),
                   '|', ('invoice_status', '=', 'to invoice'), ('invoice_status', '=', 'invoiced')]
        return res
    
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

    @api.onchange("etd")
    def _onchange_original_etd(self):
        if self.etd and (not self.etd_revised or self.etd_revised < self.etd):
            self.etd_revised = self.etd

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

    @api.constrains('etd', 'etd_revised')
    def _check_etd_revised_time(self):
        for booking in self:
            if booking.etd_revised and booking.etd and booking.etd_revised < booking.etd:
                raise ValidationError(_('The revised ETD cannot be earlier than the original ETD.'))

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("number", "#") == "#":
            max_repeat = 10
            count = 1
            shipment_number = ''
            while count <= max_repeat and not shipment_number:
                shipment_number = self._prepare_freight_booking_shptmt_number(vals)
                exist_record = self.search_count([('number', '=', shipment_number)])
                if exist_record:
                    shipment_number = ''
                count += 1
            if count > max_repeat and not shipment_number:
                raise ValidationError(_('A booking number already exists with this name. Please choose another one!'))
            vals["number"] = shipment_number
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
        for booking in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["freight.catalog.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.completed:
                    vals["completed_date"] = now
            if vals.get("user_id"):
                vals["issued_date"] = now

            """ Reset the sequence number if etd_revised changed to another month
            """
            if vals.get("etd_revised"):
                current_date = fields.Datetime.context_timestamp(self, booking.etd_revised) if booking.etd_revised else False
                new_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['etd_revised']))
                if current_date and new_date and new_date.month != current_date.month:
                    vals["number"] = self._prepare_freight_booking_shptmt_number(vals)

        return super().write(vals)

    def action_duplicate_freight_booking(self):
        for booking in self.browse(self.env.context["active_ids"]):
            booking.copy()

    def _prepare_freight_booking_shptmt_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])

        seq_date = None
        if 'etd_revised' in values and values['etd_revised']:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['etd_revised']))

        result = seq.next_by_code("freight.booking.sequence", sequence_date=seq_date) or "#"

        """ Update sequence month prefix if the month of the revised ETD is difference the current month
        Because automated sequence is always returned current month
        """
        if seq_date:
            now = fields.Datetime.context_timestamp(self, fields.Datetime.now())    # now in local time zone
            if seq_date.month != now.month:
                new_seq = result.split('-')
                if new_seq and len(new_seq) > 1:
                    seq_next = new_seq[1]
                    seq_prefix_new = seq_date.strftime('LOG%m%y-')
                    result = seq_prefix_new + seq_next

        return result

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


class FreightBookingVolume(models.Model):
    _name = 'freight.booking.volume'
    _description = 'Freight Booking Volume'
    _order = 'booking_id, sequence, id'
    _check_company_auto = True

    booking_id = fields.Many2one('freight.booking', string='Booking', index=True)
    sequence = fields.Integer(string='Sequence', default=10)
    quantity = fields.Integer(string="Quantity")
    container_id = fields.Many2one(
        comodel_name="freight.catalog.container", string="Container", ondelete="restrict", tracking=True, index=True
    )
