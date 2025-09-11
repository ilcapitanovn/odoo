# Copyright 2025 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, models


class FreightSaleReportSaleOrder(models.AbstractModel):
    _name = 'report.sale.report_saleorder'
    _description = 'Freight Sale Report Get Values'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'data': data,
            'doc_model': 'sale.order',
            'docs': docs
        }
