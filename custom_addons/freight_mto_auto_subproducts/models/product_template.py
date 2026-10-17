# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mto_subproduct_ids = fields.One2many(
        'product.template.mto.subproduct', 'template_id',
        string='MTO Auto PO Sub-Products', copy=True)
    mto_subproduct_count = fields.Integer(
        string='Sub-Products', compute='_compute_mto_subproduct_count')

    @api.depends('mto_subproduct_ids', 'mto_subproduct_ids.active')
    def _compute_mto_subproduct_count(self):
        for tmpl in self:
            tmpl.mto_subproduct_count = len(
                tmpl.mto_subproduct_ids.filtered('active'))
