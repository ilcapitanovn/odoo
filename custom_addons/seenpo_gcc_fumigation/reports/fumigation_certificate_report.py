# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, models


class FumigationCertificateReport(models.AbstractModel):
    _name = 'report.seenpo_gcc_fumigation.report_fumigation_certificate'
    _description = 'Fumigation Certificate Report Get Values'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["seenpo.fumigation.certificate"].browse(docids)
        # free_time_until = None
        # for doc in docs:
        #     eta = doc.eta
        #     if eta:
        #         storage_days = doc.storage_days
        #         free_time_until = eta + + datetime.timedelta(days=storage_days)

        return {
            'doc_ids': docids,
            'data': data,
            'docs': docs
            # 'free_time_until': free_time_until
        }
