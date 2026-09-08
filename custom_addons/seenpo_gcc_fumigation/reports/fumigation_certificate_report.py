# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, models


class FumigationCertificateReport(models.AbstractModel):
    _name = 'report.seenpo_gcc_fumigation.report_fumigation_certificate'
    _description = 'Fumigation Certificate Report Get Values'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data and data.get('active_ids'):
            doc_ids = data.get('active_ids')
        else:
            doc_ids = docids or []

        # show_signature = False
        # # Lấy bản ghi XML ID của Action "Có chữ ký" để đối chiếu
        # action_with_sign = self.env.ref('seenpo_gcc_fumigation.')
        # current_action_id = self.env.context.get('active_id') \
        #     if self.env.context.get('active_model') == 'ir.actions.report' else None
        # # Fallback: Kiểm tra qua biến data nếu Odoo gom luồng xử lý report
        # if data and data.get('id'):
        #     current_action_id = data.get('id')
        #
        # if current_action_id == action_with_sign.id:
        #     show_signature = True

        # 2. Read the custom 'no_sign' flag safely
        # no_signature = data.get('no_sign', False) if data else False

        docs = self.env["seenpo.fumigation.certificate"].browse(doc_ids)

        # 1. Lấy dữ liệu cấu hình từ Settings (kèm giá trị fallback mặc định nếu trống)
        param_obj = self.env['ir.config_parameter'].sudo()
        header_size = param_obj.get_param('seenpo_gcc_fumigation.header_font_size', default='15')
        title_size = param_obj.get_param('seenpo_gcc_fumigation.title_font_size', default='28')
        content_size = param_obj.get_param('seenpo_gcc_fumigation.content_font_size', default='16')
        signature_size = param_obj.get_param('seenpo_gcc_fumigation.signature_font_size', default='18')

        try:
            header_size_int = int(header_size)
            title_size_int = int(title_size)
            content_size_int = int(content_size)
            signature_size_int = int(signature_size)
        except (ValueError, TypeError):
            header_size_int = 15
            title_size_int = 15
            content_size_int = 15
            signature_size_int = 15

        return {
            'doc_ids': docids,
            'data': data,
            'company': self.env.company,
            'docs': docs,
            # 'print_no_sign': show_signature,

            'header_company_font_size': f"{header_size_int + 5}px",
            'header_address_font_size': f"{header_size_int}px",
            'title_font_size': f"{title_size_int}px",
            'content_font_size': f"{content_size_int}px",
            'certificate_no_font_size': f"{content_size_int}px",
            'signature_font_size': f"{signature_size_int}px",
        }


class FumigationCertificateReportWithSign(models.AbstractModel):
    _name = 'report.seenpo_gcc_fumigation.report_fumi_cert_with_sign'
    _inherit = 'report.seenpo_gcc_fumigation.report_fumigation_certificate'
    _description = 'Fumigation Certificate Report With Sign - Get Values'
