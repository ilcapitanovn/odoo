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
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """inherited sale order"""
    _inherit = 'sale.order'

    branch_id = fields.Many2one("res.branch", string='Branch', store=True, readonly=False,
                                compute="_compute_branch_id")
    allowed_branch_ids = fields.Many2many('res.branch', string="Branches", store=True,
                                          compute='_compute_allowed_branch_ids')

    @api.model
    def _init_default_sale_order_branch(self):
        branch_saigon = self.env.ref('seenpo_multi_branch_base.seenpo_branch_saigon')
        orders = self.search([])
        for order in orders:
            order.write({'branch_id': branch_saigon.id})

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

    def _prepare_invoice(self):
        """override prepare_invoice function to include branch"""
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        branch_id = self.branch_id.id
        # domain = [('branch_id', '=', branch_id),
        #           ('type', '=', 'sale'),
        #           ('code', '!=', 'POSS'), ('company_id', '=', self.company_id.id)]
        #
        # journal = None
        # if self._context.get('default_currency_id'):
        #     currency_domain = domain + [
        #         ('currency_id', '=', self._context['default_currency_id'])]
        #     journal = self.env['account.journal'].search(currency_domain,
        #                                                  limit=1)
        #
        # if not journal:
        #     journal = self.env['account.journal'].search(domain, limit=1)
        # if not journal:
        #     domain = [('type', '=', 'sale'), ('code', '!=', 'POSS'),
        #               ('branch_id', '=', False), ('company_id', '=', self.company_id.id)]
        #     journal = self.env['account.journal'].search(domain, limit=1)
        # if not journal:
        #     error_msg = _(
        #         "No journal could be found in the '%s' branch"
        #         " for any of those types: sale",
        #         self.branch_id.name,
        #     )
        #     raise UserError(error_msg)

        invoice_vals['branch_id'] = branch_id or False
        # invoice_vals['journal_id'] = journal.id
        return invoice_vals


class SaleOrderLine(models.Model):
    """inherited sale order line"""
    _inherit = 'sale.order.line'

    branch_id = fields.Many2one(related='order_id.branch_id', string='Branch', store=True)
