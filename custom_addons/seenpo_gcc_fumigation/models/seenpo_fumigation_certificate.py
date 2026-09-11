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

    @api.model
    def _default_branch_id(self):
        branch = self.env.user.branch_id
        if not branch:
            branch = self.env['res.branch'].sudo().search([('name', 'not ilike', 'Trading')], limit=1)

        return branch.id if branch else False

    @api.model
    def _default_dosage_uom(self):
        dosage_uom = self.env['uom.uom'].search([('name', '=', 'g/m³')], limit=1)
        return dosage_uom.id if dosage_uom else False

    @api.model
    def _default_exposure_time_hour_uom(self):
        exposure_hour_uom = self.env['uom.uom'].search([('name', '=', 'Hours')], limit=1)
        return exposure_hour_uom.id if exposure_hour_uom else False

    @api.model
    def _default_exposure_time_degree_uom(self):
        exposure_degree_uom = self.env['uom.uom'].search([('name', '=', '°C')], limit=1)
        return exposure_degree_uom.id if exposure_degree_uom else False

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
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True, tracking=True
    )
    is_customer_printing = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    branch_id = fields.Many2one("res.branch", string='Branch', tracking=True, store=True,
                                domain=[('name', 'not ilike', 'Trading')],
                                default=_default_branch_id)

    transport_type = fields.Selection([
        ('sea', 'Sea'),
        ('road', 'Road'),
        ('pallet', 'Wooden Pallet'),
        ('air', 'Air'),
    ], string='Transport Type', default='sea', required=True, tracking=True)

    # Shipper & Consignee
    shipper_id = fields.Many2one(comodel_name="res.partner",
                                 domain=["|", ("category_id.name", "=", "Shipper"),
                                         ('category_id.name', 'ilike', 'Người giao hàng')],
                                 string="Shipper", tracking=True)
    shipper_name = fields.Char(string="Shipper's Name", tracking=True)
    shipper_email = fields.Char(string="Shipper's Email", tracking=True)
    shipper_address = fields.Char(string="Shipper's Address", tracking=True)
    shipper_phone = fields.Char(string="Shipper's Phone", tracking=True)
    is_shipper_name_printing = fields.Boolean(default=True, help="Check to include this field in the PDF report.")
    is_shipper_address_printing = fields.Boolean(default=True)
    is_shipper_phone_printing = fields.Boolean(default=True)

    consignee_id = fields.Many2one(comodel_name="res.partner",
                                   domain=["|", ("category_id.name", "=", "Consignee"),
                                           ('category_id.name', 'ilike', 'Người nhận hàng')],
                                   string="Consignee", tracking=True)
    consignee_name = fields.Char()
    consignee_email = fields.Char(string="Consignee's Email", tracking=True)
    consignee_address = fields.Char(string="Consignee's Address", tracking=True)
    consignee_phone = fields.Char(string="Consignee's Phone", tracking=True)
    is_consignee_name_printing = fields.Boolean(default=True)
    is_consignee_address_printing = fields.Boolean(default=True)
    is_consignee_phone_printing = fields.Boolean(default=True)

    # Cargo information
    cargo_name = fields.Text(string='Name of commodity', tracking=True)
    cargo_name_short = fields.Char(string='Name of commodity', compute='_compute_cargo_name_short')
    quantity = fields.Char(string='Total Quantity', tracking=True)
    gross_weight = fields.Char(string='Weight', tracking=True)
    vessel_name = fields.Char(string='Mean of Conveyance', tracking=True)
    bl_number = fields.Char(string='Bill of Lading', tracking=True)
    port_loading_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Port of loading",
        tracking=True, index=True
    )
    port_discharge_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Port of discharge",
        tracking=True, index=True
    )
    port_loading = fields.Char(string='Port of loading', tracking=True)
    port_discharge = fields.Char(string='Port of discharge', tracking=True)
    delivery_place = fields.Char(string='Place of delivery', tracking=True)
    shipment_date = fields.Date(string='Date of shipment', tracking=True)
    container_no = fields.Char(string='Container / Seal No.', tracking=True)

    container_line = fields.One2many('seenpo.fumigation.certificate.container', 'certificate_id',
                                     string='Containers / Seals',
                                     copy=True, auto_join=True, tracking=True)

    is_cargo_name_printing = fields.Boolean(default=True)
    is_quantity_printing = fields.Boolean(default=True)
    is_gross_weight_printing = fields.Boolean(default=True)
    is_vessel_name_printing = fields.Boolean(default=True)
    is_bl_number_printing = fields.Boolean(default=True)
    is_port_loading_printing = fields.Boolean(default=True)
    is_port_discharge_printing = fields.Boolean(default=True)
    is_delivery_place_printing = fields.Boolean(default=True)
    is_shipment_date_printing = fields.Boolean(default=True)
    is_container_no_printing = fields.Boolean(default=True)

    # Fumigation parameters
    chemical_list = fields.Selection([
        ('MB', 'METHYL BROMIDE (CH₃Br)'),
        ('AC5', 'ACTELLIC 50EC'),
        ('AP', 'ALUMINUM PHOSPHIDE AT 56%')
    ], string='Chemical', default='MB', required=True, tracking=True)   # TODO: Deprecated
    chemical_id = fields.Many2one(
        'seenpo.fumigation.catalog.chemical',
        string='Chemical',
        compute='_compute_chemical_id',
        store=True,
        readonly=False,  # Allows users to manually set or edit values
        tracking=True,
        ondelete='restrict'
    )

    chemical = fields.Char(string='Chemical', default="METHYL BROMIDE (CH₃Br)", readonly=True)  # TODO: Deprecated
    fumigation_place = fields.Char(string='Fumigation Place', tracking=True)
    fumigation_date = fields.Date(string='Date of fumigation', default=date.today(), tracking=True)
    defumigation_date = fields.Date(string='Date of defumigation', tracking=True)
    dosage = fields.Char(string='Dosage Custom Text', tracking=True,
                         help="Enter a custom dosage text here to override the standard selection. If left blank, the system will default to the value selected in the dropdown list.")
    dosage_number = fields.Integer(string="Dosage", tracking=True)
    dosage_uom_id = fields.Many2one('uom.uom', string='Dosage UoM', ondelete="restrict",
                                    default=_default_dosage_uom, tracking=True)

    exposure_time = fields.Char(string='Exposure Time Custom Text', tracking=True,
                                help="Enter a custom text of exposure time here to override the standard selection. If left blank, the system will default to the value selected in the dropdown list.")
    exposure_time_hour = fields.Integer(string="Exposure Time", tracking=True)
    exposure_time_hour_uom_id = fields.Many2one('uom.uom', string='Exposure Time UoM', ondelete="restrict",
                                                default=_default_exposure_time_hour_uom, tracking=True)
    exposure_time_degree = fields.Integer(string="At Degree", tracking=True)
    exposure_time_degree_uom_id = fields.Many2one('uom.uom', string='At Degree UoM', ondelete="restrict",
                                                  default=_default_exposure_time_degree_uom, tracking=True)
    exposure_time_degree_text = fields.Char(string='Exposure Degree Custom Text', tracking=True,
                                help="Enter a custom text of exposure degree here to override the standard selection. If left blank, the system will default to the value selected in the dropdown list.")
    signer = fields.Char(string='Signer', default="TRIEU CHAT HAN", readonly=True)

    is_chemical_list_printing = fields.Boolean(default=True, readonly=True)
    is_chemical_printing = fields.Boolean(default=True, readonly=True)
    is_fumigation_place_printing = fields.Boolean(default=True)
    is_fumigation_date_printing = fields.Boolean(default=True)
    is_defumigation_date_printing = fields.Boolean(default=False)
    is_dosage_printing = fields.Boolean(default=True)
    is_exposure_time_printing = fields.Boolean(default=True)
    is_exposure_degree_printing = fields.Boolean(default=True)
    is_ispm15_printing = fields.Boolean(default=True, string="Show ISPM15")
    is_fumigation_results_printing = fields.Boolean(default=True, string="Show Fumigation Results")
    is_signer_printing = fields.Boolean(default=True, readonly=True)

    # Other
    note = fields.Text(string='Internal Notes', tracking=True)
    image_attachment = fields.Binary(
        string="Image",
        tracking=True,
        attachment=True,
        help="Upload image"
    )
    is_image_attachment_printing = fields.Boolean(default=True)

    scan_attachment = fields.Binary(
        string="File scan",
        tracking=True,
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
                seq_name = self.env['ir.sequence'].next_by_code('seenpo.fumigation.certificate.sequence') or '#'
                if rec.branch_id:
                    if rec.branch_id.code == 'LS' and seq_name.endswith('/FUM'):
                        seq_name = seq_name.replace('/FUM', '/FUM-LS')
                    elif seq_name.endswith('/FUM-LS'):
                        seq_name = seq_name.replace('/FUM-LS', '/FUM')
                rec.name = seq_name

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

    def action_print_preview(self):
        """Hàm cập nhật: Gọi model wizard để hiển thị PDF ngay trong cửa sổ popup"""
        self.ensure_one()

        # 1. Tìm bản ghi báo cáo dựa vào External ID trong XML của bạn
        report_xml_id = 'seenpo_gcc_fumigation.seenpo_action_report_fumigation_certificate_with_sign'
        report = self.env.ref(report_xml_id)

        # 2. Gọi hàm mở popup dialog từ model Transient mới tạo
        return self.env['fumigation.report.preview.wizard'].open_preview(
            report_name=report.report_name,
            res_id=self.id
        )

    def _get_updated_sequence_name(self, current_name, branch):
        """Hàm phụ trợ để hoán đổi đuôi mã dựa trên chi nhánh"""
        if not current_name or current_name == '#':
            return current_name

        # Xác định đuôi cần hiển thị dựa trên chi nhánh mới
        # Nếu là Lạng Sơn thì dùng đuôi /FUM-LS, ngược lại thì dùng mặc định /FUM
        target_suffix = '/FUM'
        if branch and branch.code == 'LS':
            target_suffix = '/FUM-LS'

        # Cắt bỏ phần đuôi cũ (bất kể đang là /FUM hay /FUM-LS) để lấy phần số gốc
        base_name = current_name
        if base_name.endswith('/FUM-LS'):
            base_name = base_name[:-7]  # Cắt 7 ký tự đuôi '/FUM-LS'
        elif base_name.endswith('/FUM'):
            base_name = base_name[:-4]  # Cắt 4 ký tự đuôi '/FUM'

        # Ghép phần số gốc với đuôi mới
        return f"{base_name}{target_suffix}"

    @api.constrains('fumigation_date', 'shipment_date')
    def _check_fumigation_before_shipment(self):
        for rec in self:
            if rec.fumigation_date and rec.shipment_date and rec.fumigation_date > rec.shipment_date:
                raise ValidationError("Date of fumigation must be before or on date of shipment.")

    @api.depends('cargo_name')
    def _compute_cargo_name_short(self):
        for record in self:
            if record.cargo_name:
                # Cắt lấy 50 ký tự đầu tiên rồi thêm dấu ba chấm
                record.cargo_name_short = record.cargo_name[:50] + '...' \
                    if len(record.cargo_name) > 50 else record.cargo_name
            else:
                record.cargo_name_short = ''

    @api.depends('chemical_list')
    def _compute_chemical_id(self):
        """Map existing selection values to new Many2one records."""
        chemicals = self.env['seenpo.fumigation.catalog.chemical'].search([])
        chemical_map = {chem.code: chem.id for chem in chemicals}

        for record in self:
            if not record.chemical_id and record.chemical_list:
                record.chemical_id = chemical_map.get(record.chemical_list)

    @api.onchange('branch_id')
    def _onchange_branch_id_update_name(self):
        """Thay đổi đuôi mã NGAY LẬP TỨC trên giao diện khi user đổi chi nhánh"""
        for rec in self:
            # Chỉ tự động đổi đuôi nếu chứng thư ĐÃ ĐƯỢC sinh số (khác draft/#)
            if rec.name and rec.name != '#':
                rec.name = self._get_updated_sequence_name(rec.name, rec.branch_id)

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
            self.is_vessel_name_printing = True
            self.is_container_no_printing = False
            self.is_bl_number_printing = False
            self.is_port_loading_printing = True
            self.is_port_discharge_printing = True
            self.is_shipment_date_printing = False

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_exposure_degree_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

            return {
                'domain': {
                    'port_loading_id': [('port_type', '=', 'land')],
                    'port_discharge_id': [('port_type', '=', 'land')],
                }
            }

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
            self.is_vessel_name_printing = False
            self.is_container_no_printing = False
            self.is_bl_number_printing = False
            self.is_port_loading_printing = False
            self.is_port_discharge_printing = False
            self.is_shipment_date_printing = False

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_exposure_degree_printing = True
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
            self.is_vessel_name_printing = True
            self.is_container_no_printing = False
            self.is_bl_number_printing = True
            self.is_port_loading_printing = True
            self.is_port_discharge_printing = True
            self.is_shipment_date_printing = True

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_exposure_degree_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

            return {
                'domain': {
                    'port_loading_id': [('port_type', '=', 'air')],
                    'port_discharge_id': [('port_type', '=', 'air')],
                }
            }

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
            self.is_vessel_name_printing = True
            self.is_container_no_printing = True
            self.is_bl_number_printing = True
            self.is_port_loading_printing = True
            self.is_port_discharge_printing = True
            self.is_shipment_date_printing = True

            # Fumigation Parameters
            self.is_dosage_printing = True
            self.is_exposure_time_printing = True
            self.is_exposure_degree_printing = True
            self.is_fumigation_place_printing = True
            self.is_fumigation_date_printing = True
            self.is_defumigation_date_printing = False

            self.is_signer_printing = True

            return {
                'domain': {
                    'port_loading_id': [('port_type', '=', 'ocean')],
                    'port_discharge_id': [('port_type', '=', 'ocean')],
                }
            }

    @api.constrains(
        'delivery_place', 'is_delivery_place_printing',
        'container_line', 'is_container_no_printing'
    )
    def _check_delivery_place_required(self):
        for record in self:
            if record.is_delivery_place_printing and not record.delivery_place:
                raise ValidationError(
                    "The 'Delivery Place' field is required when 'Is Delivery Place Printing' is checked.")

            # If the checkbox is True and the one2many field contains no records
            if record.is_container_no_printing and not record.container_line:
                raise ValidationError(
                    "You must add at least one item to the 'Containers / Seals' when it is checked."
                )

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

    def write(self, vals):
        """Đảm bảo dữ liệu được cập nhật chính xác vào Database khi bấm Save"""
        res = super(SeenpoFumigationCertificate, self).write(vals)

        # Nếu user thay đổi trường branch_id, ta kiểm tra và cập nhật lại name
        if 'branch_id' in vals:
            for rec in self:
                if rec.name and rec.name != '#':
                    # Lấy đối tượng branch mới sau khi ghi dữ liệu
                    new_name = rec._get_updated_sequence_name(rec.name, rec.branch_id)
                    # Sử dụng super().write để tránh lặp hàm vô hạn (infinite loop)
                    super(SeenpoFumigationCertificate, rec).write({'name': new_name})
        return res
