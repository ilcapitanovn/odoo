# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.http import request
import werkzeug.urls

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        result = super(ResPartner, self).default_get(fields)
        # Two ways to update a property in object
        # result.update({
        #     'user_id': self.env.uid or False
        # })
        result['user_id'] = self.env.uid or False

        return result

    has_edit_salesperson = fields.Boolean(compute="_compute_has_edit_salesperson")

    # @api.model
    # def autocomplete(self, recs, *args, **kwargs):
    #     print("_autocomplete_method called")
    #
    #     partners = self.search([('name', 'ilike', recs)], limit=20)
    #     if partners:
    #         print("existing")
    #     else:
    #         print("empty")
    #
    #     return [{
    #         'name': 'Test Auto Complete',
    #         'logo': ''
    #     }]

    def _compute_has_edit_salesperson(self):
        sale_admins = self.env['res.users'].sudo().with_context(lang='en_US').search(
            [('groups_id.name', 'ilike', 'Administrator'), ('groups_id.category_id.name', 'ilike', 'sale')])

        for rec in self:
            rec.has_edit_salesperson = False
            if sale_admins and (self.env.uid in sale_admins.ids):
                rec.has_edit_salesperson = True
                return

    # def _default_category(self):
    #     existing_tags = self.env['res.partner.category'].search([('name', '=like', 'Shipper')])
    #     # default_tag = self._context.get('default_category_id')
    #     return [(6, 0, existing_tags.ids)]
    #     # return self.env['res.partner.category'].browse(self._context.get('category_id'))
