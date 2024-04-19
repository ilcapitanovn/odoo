from odoo import _, fields, api, models
from odoo.exceptions import ValidationError


class FreightFormWO(models.Model):
    _name = "freight.form.wo"
    _description = "Freight Form WO"
    _rec_name = "export_form_number"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin"]

    def _default_business_contact(self):
        default_contact = self.env['res.partner'].sudo().search([('name', '=', 'Công ty TNHH Việt Toản Lạng Sơn')], limit=1).id
        return default_contact

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    business_contact = fields.Many2one(comodel_name="res.partner", string="Business Name",
                                       default=_default_business_contact, tracking=True)
    business_display_name = fields.Char(string="Display Name", tracking=True)
    business_vat = fields.Char(string="Tax Number", tracking=True)
    export_form_number = fields.Char(string="Custom Export No.", tracking=True)
    place_of_purchase_address = fields.Char(string="Purchasing Address", tracking=True)
    responsible_buyer = fields.Many2one(comodel_name="res.users", string="Responsible Buyer", tracking=True)
    buyer_id_number = fields.Char(string="Buyer Identity Number", tracking=True)
    applicable_criteria = fields.Char(string="Applicable Criteria", default="WO", tracking=True)
    commodity = fields.Char(string="Commodity", tracking=True)
    commodity_code = fields.Char(string="Commodity Code", help="Commodity Code (6 No.)", size=6, tracking=True)
    quantity = fields.Float(string='Quantity (kg)', tracking=True)
    value_daf = fields.Monetary(string='DAF Value (USD)', tracking=True)

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

    form_wo_items = fields.One2many('freight.form.wo.line', 'form_wo_id', string='Form WO Items',
                                    store=True, copy=True, tracking=True, auto_join=True)

    description = fields.Char(translate=True)
    active = fields.Boolean(default=True)

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         result.append((rec.id, rec.code + " - " + rec.name))
    #     return result

    @api.constrains("commodity_code")
    def _check_commodity_code(self):
        for record in self:
            if record.commodity_code and (len(record.commodity_code) != 6 or not record.commodity_code.isdigit()):
                raise ValidationError(_("Commodity code must be 6 digits."))

    @api.onchange("business_contact")
    def _onchange_business_contact(self):
        if self.business_contact:
            self.business_display_name = self.business_contact.name
            self.business_vat = self.business_contact.vat

    @api.onchange("responsible_buyer")
    def _onchange_responsible_buyer(self):
        if self.responsible_buyer and self.responsible_buyer.employee_id:
            self.buyer_id_number = self.responsible_buyer.employee_id.identification_id
