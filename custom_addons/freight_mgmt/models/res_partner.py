# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.http import request
import werkzeug.urls

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_category(self):
        existing_tags = self.env['res.partner.category'].search([('name', '=like', 'Shipper')])
        # default_tag = self._context.get('default_category_id')
        return [(6, 0, existing_tags.ids)]
        # return self.env['res.partner.category'].browse(self._context.get('category_id'))

    # category_id = fields.Many2many('res.partner.category', column1='partner_id',
    #                                column2='category_id', string='Tags', default=_default_category)


    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     menu_id = self._context.get('menu_id', False)
    #     action = self._context.get('action', False)
    #     res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                            submenu=submenu)
    #     return res

    # @api.model
    # def default_get(self, fields):
    #     rec = super(ResPartner, self).default_get(fields)
    #     active_model = self.env.context.get('active_model')
    #     rec['website'] = "test.shipper.com"
    #     if active_model == 'crm.lead' and len(self.env.context.get('active_ids', [])) <= 1:
    #         lead = self.env[active_model].browse(self.env.context.get('active_id')).exists()
    #         if lead:
    #             rec.update(
    #                 phone=lead.phone,
    #                 mobile=lead.mobile,
    #                 function=lead.function,
    #                 title=lead.title.id,
    #                 website=lead.website,
    #                 street=lead.street,
    #                 street2=lead.street2,
    #                 city=lead.city,
    #                 state_id=lead.state_id.id,
    #                 country_id=lead.country_id.id,
    #                 zip=lead.zip,
    #             )
    #     return rec

    # def _compute_opportunity_count(self):
    #     # retrieve all children partners and prefetch 'parent_id' on them
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
    #     all_partners.read(['parent_id'])
    #
    #     opportunity_data = self.env['crm.lead'].with_context(active_test=False).read_group(
    #         domain=[('partner_id', 'in', all_partners.ids)],
    #         fields=['partner_id'], groupby=['partner_id']
    #     )
    #
    #     self.opportunity_count = 0
    #     for group in opportunity_data:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             if partner in self:
    #                 partner.opportunity_count += group['partner_id_count']
    #             partner = partner.parent_id

    # def action_view_opportunity(self):
    #     '''
    #     This function returns an action that displays the opportunities from partner.
    #     '''
    #     action = self.env['ir.actions.act_window']._for_xml_id('crm.crm_lead_opportunities')
    #     action['context'] = {'active_test': False}
    #     if self.is_company:
    #         action['domain'] = [('partner_id.commercial_partner_id.id', '=', self.id)]
    #     else:
    #         action['domain'] = [('partner_id.id', '=', self.id)]
    #     return action

    # @api.model
    # def create(self, vals):
    #     # existing_tags = self.env['res.partner.category'].search([('name', '=like', 'Shipper')])
    #     # if existing_tags:
    #     #     vals['category_id'] = [(6, 0, existing_tags.ids)]
    #     return super(ResPartner, self).create(vals)
    #
    # def write(self, vals):
    #     # existing_tags = self.env['res.partner.category'].search([('name', '=like', 'Shipper')])
    #     # if existing_tags:
    #     #     vals['category_id'] = [(6, 0, existing_tags.ids)]
    #     return super(ResPartner, self).write(vals)