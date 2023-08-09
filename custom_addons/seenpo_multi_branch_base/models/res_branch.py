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

import logging
from odoo import _, api, models, fields
from odoo.osv import expression
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Branch(models.Model):
    """res branch"""
    _name = "res.branch"
    _description = 'Company Branches'
    _order = 'name'

    code = fields.Char(string='Code', required=True, store=True)
    name = fields.Char(string='Branch Name', required=True, store=True, translate=True)
    is_main_branch = fields.Boolean(string="Main Branch", required=True, store=True, default=False)
    company_id = fields.Many2one('res.company', required=True, string='Company')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        'res.country.state',
        string="Fed. State", domain="[('country_id', '=?', country_id)]"
    )
    country_id = fields.Many2one('res.country',  string="Country")
    email = fields.Char(store=True)
    phone = fields.Char(store=True)
    website = fields.Char(readonly=False)

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', 'The Code must be unique !')
    # ]
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The Code must be unique !')
    ]

    @api.onchange('is_main_branch')
    def _onchange_is_main_branch(self):
        if self.is_main_branch:
            existing_main = self.env['res.branch'].sudo().search([('is_main_branch', '=', True)], limit=1)
            if len(existing_main) > 0:
                warning = {
                    'title': 'Error',
                    'message': _('Only one branch is marked as the main branch. Please remove the other first!')
                }
                return {'warning': warning, 'value': {'is_main_branch': False}}

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = [('name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)