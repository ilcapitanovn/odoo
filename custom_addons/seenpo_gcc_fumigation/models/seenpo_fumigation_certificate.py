# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import date
from odoo.exceptions import UserError, ValidationError
import uuid


class SeenpoFumigationCertificate(models.Model):
    _name = 'seenpo.fumigation.certificate'
    _description = 'GCC Fumigation Certificate'
    _order = 'fumigation_date desc, id desc'
    _mail_post_access = "read"
    _inherit = ["portal.mixin", "mail.thread.cc", "mail.activity.mixin"]

    name = fields.Char(
        string='Certificate Number',
        required=True,
        copy=False,
        default=lambda self: _('#'),
    )
    heading = fields.Char(string="Certificate Heading", required=True,
                          default="Certificate of Fumigation", tracking=True)

    qr_token = fields.Char(
        string='QR Token',
        readonly=True,
        copy=False,
    )

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
    )
    is_customer_printing = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string="Partner")

    transport_type = fields.Selection([
        ('sea', 'Sea'),
        ('road', 'Road'),
        ('pallet', 'Wooden Pallet'),
        ('air', 'Air'),
    ], string='Transport Type', default='sea', required=True)

    # Shipper & Consignee
    shipper_id = fields.Many2one(comodel_name="res.partner",
                                 domain=["|", ("category_id.name", "=", "Shipper"),
                                         ('category_id.name', 'ilike', 'Người giao hàng')],
                                 string="Shipper", tracking=True)
    shipper_name = fields.Char(string="Shipper's Name")
    shipper_email = fields.Char(string="Shipper's Email")
    shipper_address = fields.Char(string="Shipper's Address", tracking=True)
    shipper_phone = fields.Char(string="Shipper's Phone", tracking=True)
    is_shipper_name_printing = fields.Boolean(default=True)
    is_shipper_address_printing = fields.Boolean(default=True)
    is_shipper_phone_printing = fields.Boolean(default=True)

    consignee_id = fields.Many2one(comodel_name="res.partner",
                                   domain=["|", ("category_id.name", "=", "Consignee"),
                                           ('category_id.name', 'ilike', 'Người nhận hàng')],
                                   string="Consignee", tracking=True)
    consignee_name = fields.Char()
    consignee_email = fields.Char(string="Consignee's Email")
    consignee_address = fields.Char(string="Consignee's Address", tracking=True)
    consignee_phone = fields.Char(string="Consignee's Phone", tracking=True)
    is_consignee_name_printing = fields.Boolean(default=True)
    is_consignee_address_printing = fields.Boolean(default=True)
    is_consignee_phone_printing = fields.Boolean(default=True)

    # Cargo information
    cargo_name = fields.Text(string='Name of commodity')
    quantity = fields.Char(string='Total Quantity')
    gross_weight = fields.Char(string='Weight')
    vessel_name = fields.Char(string='Mean of Conveyance')
    bl_number = fields.Char(string='Bill of Lading')
    # port_loading_id = fields.Many2one(
    #     comodel_name="freight.catalog.port", string="Port of loading",
    #     required=True, tracking=True, index=True
    # )
    # port_discharge_id = fields.Many2one(
    #     comodel_name="freight.catalog.port", string="Port of discharge",
    #     required=True, tracking=True, index=True
    # )
    port_loading = fields.Char(string='Port of loading')
    port_discharge = fields.Char(string='Port of discharge')
    shipment_date = fields.Date(string='Date of shipment')
    container_no = fields.Char(string='Container / Seal No.')

    is_cargo_name_printing = fields.Boolean(default=True)
    is_quantity_printing = fields.Boolean(default=True)
    is_gross_weight_printing = fields.Boolean(default=True)
    is_vessel_name_printing = fields.Boolean(default=True)
    is_bl_number_printing = fields.Boolean(default=True)
    is_port_loading_printing = fields.Boolean(default=True)
    is_port_discharge_printing = fields.Boolean(default=True)
    is_shipment_date_printing = fields.Boolean(default=True)
    is_container_no_printing = fields.Boolean(default=True)

    # Fumigation parameters
    chemical_list = fields.Selection([
        ('MB', 'METHYL BROMIDE (CH₃Br)'),
        ('AC5', 'ACTELLIC 50EC'),
        ('AP', 'ALUMINUM PHOSPHIDE AT 56%')
    ], string='Chemical', default='MB', required=True)

    chemical = fields.Char(string='Chemical', default="METHYL BROMIDE (CH₃Br)", readonly=True)
    fumigation_place = fields.Char(string='Fumigation Place')
    fumigation_date = fields.Date(string='Date of fumigation', default=date.today())
    defumigation_date = fields.Date(string='Date of defumigation')
    dosage = fields.Char(string='Dosage')
    exposure_time = fields.Char(string='Exposure Time')
    signer = fields.Char(string='Signer', default="TRIEU CHAT HAN", readonly=True)

    is_chemical_list_printing = fields.Boolean(default=True, readonly=True)
    is_chemical_printing = fields.Boolean(default=True, readonly=True)
    is_fumigation_place_printing = fields.Boolean(default=True)
    is_fumigation_date_printing = fields.Boolean(default=True)
    is_defumigation_date_printing = fields.Boolean(default=False)
    is_dosage_printing = fields.Boolean(default=True)
    is_exposure_time_printing = fields.Boolean(default=True)
    is_signer_printing = fields.Boolean(default=True, readonly=True)

    # Other
    note = fields.Text(string='Internal Notes')
    image_attachment = fields.Binary(
        string="Image",
        attachment=True,
        help="Upload image"
    )
    is_image_attachment_printing = fields.Boolean(default=True)

    scan_attachment = fields.Binary(
        string="File scan",
        attachment=True,
        help="Attach scanned photos or related documents."
    )
    scan_filename = fields.Char(string="File name")

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Pending'),
            ('approved', 'Approved'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    def action_submit(self):
        self.state = 'submitted'

    def action_approve(self):
        if not self.env.user.has_group('seenpo_gcc_fumigation.group_seenpo_fumigation_manager'):
            raise UserError("Only manager can approve.")

        for rec in self:
            if rec.state == 'draft' or rec.state == 'submitted':
                # Sinh số chứng thư
                rec.name = self.env['ir.sequence'].next_by_code('seenpo.fumigation.certificate.sequence') or '#'
                # Sinh mã QR
                rec.qr_token = uuid.uuid4().hex
                rec.state = 'approved'

    def action_cancel(self):
        if not self.env.user.has_group('seenpo_gcc_fumigation.group_seenpo_fumigation_manager'):
            raise UserError("Only manager can cancel.")
        for rec in self:
            if not (rec.name and rec.name != '#'):
                rec.active = False      # Set record inactive if not approved yet
            rec.state = 'cancelled'

    @api.constrains('fumigation_date', 'shipment_date')
    def _check_fumigation_before_shipment(self):
        for rec in self:
            if rec.fumigation_date and rec.shipment_date and rec.fumigation_date > rec.shipment_date:
                raise ValidationError("Date of fumigation must be before or on date of shipment.")

    @api.onchange("shipper_id")
    def _onchange_shipper_id(self):
        if self.shipper_id:
            self.shipper_name = self.shipper_id.name
            self.shipper_email = self.shipper_id.email
            self.shipper_address = self.shipper_id.contact_address
            self.shipper_phone = self.shipper_id.phone

            if self.shipper_address:
                self.shipper_address = self.shipper_address.replace(self.shipper_name, '')

            if not self.shipper_phone:
                self.shipper_phone = self.shipper_id.mobile

    @api.onchange("consignee_id")
    def _onchange_consignee_id(self):
        if self.consignee_id:
            self.consignee_name = self.consignee_id.name
            self.consignee_email = self.consignee_id.email
            self.consignee_address = self.consignee_id.contact_address
            self.consignee_phone = self.consignee_id.phone

            if self.consignee_address:
                self.consignee_address = self.consignee_address.replace(self.consignee_name, '')

            if not self.consignee_phone:
                self.consignee_phone = self.consignee_id.mobile

    @api.onchange("transport_type")
    def _onchange_transport_type(self):
        if self.transport_type == 'road':
            # Shipper & Consignee
            self.is_shipper_name_printing = False
            self.is_shipper_address_printing = False
            self.is_shipper_phone_printing = False

            self.is_consignee_name_printing = False
            self.is_consignee_address_printing = False
            self.is_consignee_phone_printing = False

            # Cargo Information
            self.is_cargo_name_printing = True
            self.is_quantity_printing = True
            self.is_gross_weight_printing = True
            #self.is_mean_conveyance_printing = True     # TODO: Confirm Han
            self.is_container_no_printing = False
            self.is_bl_number_printing = False
            self.is_port_loading_printing = True
            #self.is_port_discharge_printing = ???      # TODO: Confirm Han
            self.is_shipment_date_printing = False

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

        elif self.transport_type == 'pallet':
            # Shipper & Consignee
            self.is_shipper_name_printing = True
            self.is_shipper_address_printing = True
            self.is_shipper_phone_printing = False

            self.is_consignee_name_printing = False
            self.is_consignee_address_printing = False
            self.is_consignee_phone_printing = False

            # Cargo Information
            self.is_cargo_name_printing = True
            self.is_quantity_printing = True
            self.is_gross_weight_printing = False
            # self.is_mean_conveyance_printing = False     # TODO: Confirm Han
            self.is_container_no_printing = False
            self.is_bl_number_printing = False
            self.is_port_loading_printing = False
            self.is_port_discharge_printing = False
            self.is_shipment_date_printing = False

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

        elif self.transport_type == 'air':
            # Shipper & Consignee
            self.is_shipper_name_printing = True
            self.is_shipper_address_printing = True
            self.is_shipper_phone_printing = False

            self.is_consignee_name_printing = True
            self.is_consignee_address_printing = True
            self.is_consignee_phone_printing = False

            # Cargo Information
            self.is_cargo_name_printing = True
            self.is_quantity_printing = True
            self.is_gross_weight_printing = True
            # self.is_mean_conveyance_printing = True     # TODO: Confirm Han
            self.is_container_no_printing = False
            self.is_bl_number_printing = True
            self.is_port_loading_printing = True
            self.is_port_discharge_printing = True
            self.is_shipment_date_printing = True

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

        else:   # 'sea'
            # Shipper & Consignee
            self.is_shipper_name_printing = True
            self.is_shipper_address_printing = True
            self.is_shipper_phone_printing = False

            self.is_consignee_name_printing = True
            self.is_consignee_address_printing = True
            self.is_consignee_phone_printing = False

            # Cargo Information
            self.is_cargo_name_printing = True
            self.is_quantity_printing = True
            self.is_gross_weight_printing = True
            # self.is_mean_conveyance_printing = True     # TODO: Confirm Han
            self.is_container_no_printing = True
            self.is_bl_number_printing = True
            self.is_port_loading_printing = True
            self.is_port_discharge_printing = True
            self.is_shipment_date_printing = True

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

    @api.model
    def create(self, vals):
        # if vals.get('name', _('New')) == _('New'):
        #     seq = self.env['ir.sequence'].next_by_code(
        #         'seenpo.fumigation.certificate.sequence'
        #     ) or _('New')
        #     vals['name'] = seq
        # if not vals.get('qr_token'):
        #     vals['qr_token'] = uuid.uuid4().hex
        return super(SeenpoFumigationCertificate, self).create(vals)
