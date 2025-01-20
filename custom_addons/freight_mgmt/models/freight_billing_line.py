# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round


class FreightBillingLine(models.Model):
    _name = 'freight.billing.line'
    _description = 'Freight Billing Line'
    _order = 'billing_id, sequence, id'
    _check_company_auto = True

    billing_id = fields.Many2one('freight.billing', string='Billing Reference', required=True, ondelete='cascade',
                                 index=True, copy=False, tracking=True)
    name = fields.Text(string='Name', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)

    container_no = fields.Text(string='Container No.', tracking=True)
    seal_nos = fields.Text(string='Seal No.', tracking=True)
    number_packages = fields.Text(string='Number of Packages')     # Deprecated
    packages_number = fields.Float(string='Number of Packages', tracking=True)
    package_types = fields.Text(string='Package Types', tracking=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', ondelete="restrict", tracking=True)
    product_uom_readonly = fields.Boolean(compute='_compute_product_uom_readonly')
    description = fields.Text(string='Description', tracking=True)
    gross_weight = fields.Float(string='Gross Weight (KGS)', tracking=True)
    net_weight = fields.Float(string='Net Weight (KGS)', tracking=True)
    measurement = fields.Text(string='Measurement')     # Deprecated
    measurement_cbm = fields.Float(string='Measurement (CBM)', tracking=True)

    company_id = fields.Many2one(related='billing_id.company_id', string='Company', store=True, index=True)
    branch_id = fields.Many2one(related="billing_id.branch_id", string='Branch')

    state = fields.Selection(
        related='billing_id.state', string='Billing Status', copy=False, store=True)

    @api.depends('state')
    def _compute_product_uom_readonly(self):
        for line in self:
            line.product_uom_readonly = line.state in ['posted', 'cancel']
