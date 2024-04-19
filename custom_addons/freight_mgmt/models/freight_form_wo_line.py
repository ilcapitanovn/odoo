from odoo import fields, api, models


class FreightFormWOLine(models.Model):
    _name = "freight.form.wo.line"
    _description = "Freight Form WO Line"
    _order = 'form_wo_id, sequence, id'
    _check_company_auto = True

    form_wo_id = fields.Many2one('freight.form.wo', string='Form WO Reference', required=True, ondelete='cascade',
                                 index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)

    buy_date = fields.Datetime(string="Buy Date", tracking=True)
    seller = fields.Many2one(comodel_name="res.partner", string="Seller", tracking=True)
    seller_address = fields.Char(string="Address", tracking=True)
    seller_id_number = fields.Char(string="ID No", tracking=True)
    commodity = fields.Char(string="Commodity", tracking=True)
    commodity_code = fields.Char(string="Commodity Code", help="Commodity Code (6 No.)", size=6, tracking=True)
    place_of_farm = fields.Char(string="Source", help="Place of exploitation, fishing and farming.", tracking=True)
    quantity = fields.Float(string='Qty (kg)', tracking=True)
    unit_price = fields.Float(string='Price', tracking=True)
    price_total = fields.Float(string='Total', compute="_compute_total", store=True)
    note = fields.Char(string="Note", tracking=True)

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         result.append((rec.id, rec.code + " - " + rec.name))
    #     return result

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for line in self:
            line.price_total = line.quantity * line.unit_price

    @api.onchange('seller')
    def _onchange_seller(self):
        if self.seller:
            self.seller_address = self.seller.contact_address
