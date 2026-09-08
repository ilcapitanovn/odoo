# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_type = fields.Selection(
        selection_add=[
            ('fumigation', 'Fumigation')
        ],
        # ondelete={'fumigation': 'set default'},
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}
    )
