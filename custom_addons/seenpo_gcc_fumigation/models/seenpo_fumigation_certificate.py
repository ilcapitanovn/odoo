# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import date
from odoo.exceptions import UserError
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
        default=lambda self: _('New'),
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
    cargo_name = fields.Char(string='Cargo Name')
    quantity = fields.Char(string='Total Quantity')
    gross_weight = fields.Char(string='Gross Weight')
    vessel_name = fields.Char(string='Vessel Name')
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
    chemical = fields.Char(string='Chemical', default="METHYL BROMIDE (CH₃Br)", readonly=True)
    fumigation_place = fields.Char(string='Fumigation Place')
    fumigation_date = fields.Date(string='Fumigation Date', default=date.today())
    dosage = fields.Char(string='Dosage')
    exposure_time = fields.Char(string='Exposure Time')
    signer = fields.Char(string='Signer', default="TRIEU CHAT HAN", readonly=True)

    is_chemical_printing = fields.Boolean(default=True, readonly=True)
    is_fumigation_place_printing = fields.Boolean(default=True)
    is_fumigation_date_printing = fields.Boolean(default=True)
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
        self.state = 'approved'

    def action_cancel(self):
        if not self.env.user.has_group('seenpo_gcc_fumigation.group_seenpo_fumigation_manager'):
            raise UserError("Only manager can cancel.")
        self.state = 'cancelled'

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

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code(
                'seenpo.fumigation.certificate.sequence'
            ) or _('New')
            vals['name'] = seq
        if not vals.get('qr_token'):
            vals['qr_token'] = uuid.uuid4().hex
        return super(SeenpoFumigationCertificate, self).create(vals)
