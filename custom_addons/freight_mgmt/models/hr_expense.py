# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class FreightHrExpense(models.Model):
    _inherit = "hr.expense"

    billing_id = fields.Many2one(comodel_name="freight.billing", string="B/L Reference", tracking=True)
    vessel_bol_number = fields.Char(related="billing_id.vessel_bol_number", string="B/L Number", readonly=True)
    related_partner_id = fields.Many2one(related="billing_id.partner_id", string="Customer", readonly=True)
