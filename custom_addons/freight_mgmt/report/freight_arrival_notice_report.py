# Copyright 2025 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, models


class FreightArrivalNoticeReport(models.AbstractModel):
    _name = 'report.freight_mgmt.report_print_arrival_notice_template'
    _description = 'Freight Arrival Notice Report Get Values'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["freight.debit.note"].browse(docids)
        free_time_until = None
        for doc in docs:
            eta = doc.eta
            if eta:
                storage_days = doc.storage_days
                free_time_until = eta + + datetime.timedelta(days=storage_days)

        return {
            'doc_ids': docids,
            'data': data,
            'docs': docs,
            'free_time_until': free_time_until
        }
