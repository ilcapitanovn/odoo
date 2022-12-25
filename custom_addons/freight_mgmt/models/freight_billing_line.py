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

    billing_id = fields.Many2one('freight.billing', string='Billing Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Name')
    sequence = fields.Integer(string='Sequence', default=10)

    container_no = fields.Text(string='Container No.')
    seal_nos = fields.Text(string='Seal No.')
    number_packages = fields.Text(string='Number of Packages')     # Deprecated
    packages_number = fields.Float(string='Number of Packages')
    package_types = fields.Text(string='Package Types')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', ondelete="restrict")
    product_uom_readonly = fields.Boolean(compute='_compute_product_uom_readonly')
    description = fields.Text(string='Description')
    gross_weight = fields.Float(string='Gross Weight (KGS)')
    measurement = fields.Text(string='Measurement')     # Deprecated
    measurement_cbm = fields.Float(string='Measurement (CBM)')

    company_id = fields.Many2one(related='billing_id.company_id', string='Company', store=True, index=True)

    state = fields.Selection(
        related='billing_id.state', string='Billing Status', copy=False, store=True)

    @api.depends('state')
    def _compute_product_uom_readonly(self):
        for line in self:
            line.product_uom_readonly = line.state in ['posted', 'cancel']
