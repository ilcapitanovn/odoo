# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    vendor_commission_amount = fields.Float(string="Comm.", store=True, tracking=True,
                                            help="Vendor Commission Amount")

    @api.onchange('seller_ids')
    def _onchange_suppliers(self):
        if not self.seller_ids:
            return

        if len(self.seller_ids) > 1:
            ''' Get the first supplier '''
            sorted_sellers = sorted(self.seller_ids, key=lambda x: x.sequence)
            first_seller = sorted_sellers[0]
            new_comm = first_seller.commission_amount_custom
        else:
            new_comm = self.seller_ids.commission_amount_custom

        if new_comm > 0:
            self.vendor_commission_amount = new_comm
        else:
            self.vendor_commission_amount = 0.0


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    def _get_default_commission_amount_custom(self):
        return self.commission_amount

    commission_id = fields.Many2one(related="name.commission_id", string="Commission", readonly=True, store=False)
    commission_amount = fields.Float(compute="_compute_commission_amount", string="Comm.", store=True)
    commission_amount_custom = fields.Float(string="Comm. Amount", default=_get_default_commission_amount_custom,
                                            store=True, tracking=True)

    @api.onchange('commission_amount')
    def _onchange_commission_amount(self):
        self.commission_amount_custom = self.commission_amount

    @api.depends('price', 'commission_id.fix_qty')
    def _compute_commission_amount(self):
        for rec in self:
            if rec.commission_id and rec.commission_id.active:
                rec.commission_amount = rec.commission_id.fix_qty * rec.price / 100
            else:
                rec.commission_amount = 0.0
