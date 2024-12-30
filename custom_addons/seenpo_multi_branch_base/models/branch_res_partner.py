# -*- coding: utf-8 -*-
#############################################################################
#
#    Bao Thinh Software Ltd.
#
#    Copyright (C) 2023-TODAY Bao Thinh Software(<https://www.baothinh.com>)
#    Author: Bao Thinh Software - Tuan Huynh(<https://www.baothinh.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class ResPartner(models.Model):
    """inherited partner"""
    _inherit = "res.partner"

    branch_id = fields.Many2one("res.branch", string='Branch', store=True, tracking=True,
                                compute="_compute_branch_id",
                                help='Leave this field empty if the partner is shared between all branches'
                                )
    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Branches",
                                          compute='_compute_allowed_branch_ids')

    @api.model
    def _init_default_partner_branch(self):
        branch_saigon = self.env.ref('seenpo_multi_branch_base.seenpo_branch_saigon')
        partners = self.search([])
        for partner in partners:
            partner.write({'branch_id': branch_saigon.id})

    @api.depends('company_id')
    def _compute_branch_id(self):
        branch = self.env.user.branch_id
        if not branch:
            branches = self.env.user.branch_ids
            if len(branches) >= 1:
                branch = branches[0]

        for rec in self:
            if branch:
                rec.branch_id = branch.ids[0]
            else:
                rec.branch_id = False

    @api.depends('company_id', 'user_id.branch_ids')
    def _compute_allowed_branch_ids(self):
        for po in self:
            po.allowed_branch_ids = self.env.user.branch_ids.ids

    # @api.model
    # def default_get(self, default_fields):
    #     """Add the company of the parent as default if we are creating a
    #     child partner.Also take the parent lang by default if any, otherwise,
    #     fallback to default DB lang."""
    #     values = super().default_get(default_fields)
    #     parent = self.env["res.partner"]
    #     if 'parent_id' in default_fields and values.get('parent_id'):
    #         parent = self.browse(values.get('parent_id'))
    #         values['branch_id'] = parent.branch_id.id
    #     return values

    @api.onchange('parent_id', 'branch_id')
    def _onchange_parent_id(self):
        """methode to set branch on changing the parent company"""
        if self.parent_id:
            self.branch_id = self.parent_id.branch_id.id

    def write(self, vals):
        """override write methode"""
        if vals.get('branch_id'):
            branch_id = vals['branch_id']
            for partner in self:
                # if partner.child_ids:
                for child in partner.child_ids:
                    child.write({'branch_id': branch_id})
        else:
            for partner in self:
                # if partner.child_ids:
                for child in partner.child_ids:
                    child.write({'branch_id': False})
        result = super(ResPartner, self).write(vals)
        return result
