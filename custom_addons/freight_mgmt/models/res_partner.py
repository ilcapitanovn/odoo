# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.http import request
import werkzeug.urls

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Overriding fields to enforce chatter history tracking of credit limit settings.
    warning_stage = fields.Monetary(tracking=True)
    blocking_stage = fields.Monetary(tracking=True)

    due_date_basis = fields.Selection(
        selection=[
            ('invoice_date', 'Invoice Date'),
            ('shipment_etd', 'Shipment ETD'),
        ],
        string='Due Date Basis',
        default='invoice_date',
        help="Reference date used to calculate this customer's invoice due date:\n"
             "- Invoice Date: standard behaviour (Invoice Date + Payment Term).\n"
             "- Shipment ETD: uses the Shipment ETD of the booking linked "
             "to the invoice instead of the Invoice Date, keeping the same "
             "Payment Term day offsets. If no booking / ETD is available on "
             "the invoice, the Invoice Date is used automatically.",
    )
    total_due_amount = fields.Monetary(
        string='Total Due',
        compute='_compute_total_due_amount',
        currency_field='currency_id'
    )
    has_debt = fields.Boolean(
        string='Has Debt',
        compute='_compute_has_debt',
        search='_search_has_debt',
    )

    def _compute_total_due_amount(self):
        for partner in self:
            # Aggregate total overdue/due amount from aging model
            aging_records = self.env['res.partner.aging.customer'].search([
                ('partner_id', '=', partner.id)
            ])
            partner.total_due_amount = sum(aging_records.mapped('total'))

    def compute_due_amount(self):
        """ Override compute due_amount from credit_limit.py in base_accounting_kit to use
        the aging model instead of credit/debit fields. """
        for rec in self:
            if not rec.id:
                continue
            rec.due_amount = rec.total_due_amount

    @api.depends('total_due_amount')
    def _compute_has_debt(self):
        for partner in self:
            partner.has_debt = partner.total_due_amount > 0

    def _search_has_debt(self, operator, value):
        """ Allows the filter in Search View to use standard ORM search """
        aging_records = self.env['res.partner.aging.customer'].search([('total', '>', 0)])
        partner_ids = aging_records.mapped('partner_id.id')

        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', partner_ids)]
        return [('id', 'not in', partner_ids)]

    def action_view_partner_debt_details(self):
        """ Opens the list of debt/aging details for this specific customer """
        self.ensure_one()
        return {
            'name': f'Debt Details - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.aging.customer',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

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

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if "due_date_basis" in vals:
            # Locate all draft invoices belonging to the modified partners
            draft_invoices = self.env["account.move"].search([
                ("partner_id", "in", self.ids),
                ("state", "=", "draft"),
                ("move_type", "in", ("out_invoice", "in_invoice", "out_refund", "in_refund")),
            ])
            # if draft_invoices:
            # Force payment term lines and due date recomputations
            # Iterate over each record individually to satisfy self.ensure_one()
            for invoice in draft_invoices:
                invoice._recompute_payment_terms_lines()
        return res
