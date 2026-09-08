# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo import SUPERUSER_ID


ALLOWED_DOMAINS = [
    "http://giamdinhtoancau.com",
    "http://www.giamdinhtoancau.com",
    "https://giamdinhtoancau.com",
    "https://www.giamdinhtoancau.com",
    # thêm domain khác nếu cần
]


class FumigationCertificateController(http.Controller):

    @http.route('/fumigation/api/v1/<string:token>', type='http', auth='public')
    def get_certificate_by_token(self, token=None, **kwargs):

        # Lấy Origin hoặc Referer
        origin = request.httprequest.headers.get('Origin')
        referer = request.httprequest.headers.get('Referer')

        # Kiểm tra domain hợp lệ
        if origin and origin not in ALLOWED_DOMAINS:
            return request.make_response(
                "403 Forbidden: Invalid Origin",
                headers=[('Content-Type', 'text/plain')],
                status=403
            )

        if referer:
            valid = False
            for domain in ALLOWED_DOMAINS:
                if referer.startswith(domain):
                    valid = True
                    break
            if not valid:
                return request.make_response(
                    "403 Forbidden: Invalid Referer",
                    headers=[('Content-Type', 'text/plain')],
                    status=403
                )

        # Tìm chứng thư theo token
        certificate = request.env['seenpo.fumigation.certificate'].sudo().search([
            ('qr_token', '=', token)
        ], limit=1)

        if not certificate:
            return request.not_found()

        # 2. TẠO MÔI TRƯỜNG SUPERUSER THUẦN TÚY (ĐÂY LÀ ĐIỂM QUAN TRỌNG)
        # Thay vì dùng môi trường của public user, ta tạo hẳn một môi trường chạy bằng ID = 4 (OdooBot/Superuser)
        su_env = request.env(user=SUPERUSER_ID)

        # Render PDF
        report_service = su_env.ref('seenpo_gcc_fumigation.seenpo_action_report_fumigation_certificate_with_sign')

        # Duyệt tìm lại record inside su_env để đảm bảo toàn bộ các trường liên kết (container_line, shipper_id)
        # khi được gọi trong QWeb XML sẽ chạy hoàn toàn bằng quyền Superuser.
        pdf_content, _ = report_service._render_qweb_pdf(certificate.with_env(su_env).ids)

        # headers = [
        #     ('Content-Type', 'application/pdf'),
        #     ('Content-Length', str(len(pdf_content))),
        #     ('Content-Disposition', 'inline; filename="certificate_%s.pdf"' % token)
        # ]
        #
        # return request.make_response(pdf_content, headers=headers)

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', str(len(pdf_content))),
            ('Content-Disposition', 'inline; filename="certificate_%s.pdf"' % token),
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
            ('Pragma', 'no-cache'),
            ('Expires', '0'),
        ]
        return request.make_response(pdf_content, headers=pdfhttpheaders)
