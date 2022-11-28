# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleCommission(models.Model):
    _inherit = "sale.commission"

    fix_qty_max = fields.Float(string="Fixed percentage Max")

    @api.constrains('fix_qty', 'fix_qty_max')
    def _check_fix_qty_max(self):
        for rec in self:
            if rec.commission_type == 'fixed' and rec.fix_qty > rec.fix_qty_max:
                raise ValidationError(_('The fixed percentage cannot be greater than the fixed percentage max.'))
