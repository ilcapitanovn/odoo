# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class FumigationReportPreviewWizard(models.TransientModel):
    _name = 'fumigation.report.preview.wizard'
    _description = 'Report Print Preview Popup'

    # Lưu trữ tên báo cáo và ID của chứng thư
    report_name = fields.Char(string='Report Name')
    res_id = fields.Integer(string='Resource ID')

    # BẮT BUỘC: Đặt sanitize=False để Odoo không tự ý xóa thẻ iframe của bạn
    pdf_iframe = fields.Html(string='PDF Preview', compute='_compute_pdf_iframe', sanitize=False)

    @api.depends('report_name', 'res_id')
    def _compute_pdf_iframe(self):
        """Hàm tính toán động sinh mã iframe trực tiếp khi popup mở ra"""
        for rec in self:
            if rec.report_name and rec.res_id:
                # 1. Tìm bản ghi chứng thư thực tế để lấy Số chứng thư (Certificate Number)
                # Lấy số chứng thư (Ví dụ: "2609360006-FUM"), loại bỏ các dấu gạch chéo '/' nếu có để tránh lỗi URL
                cert_record = self.env['seenpo.fumigation.certificate'].browse(rec.res_id)
                cert_name = (cert_record.name or '').replace('/', '-')

                # Tạo tên file mong muốn xuất hiện trên thanh công cụ
                target_filename = f"Certificate_of_Fumigation_{cert_name}.pdf"

                # 2. SỬ DỤNG CỔNG ROUTING CHUẨN KÈM THAM SỐ TÊN FILE
                # Đường dẫn này giữ đúng cấu trúc /<report_name>/<id> để Odoo không bị lạc đường sang module Website
                # Thêm tham số ẩn # để đánh lừa bộ lọc tiêu đề của trình duyệt Chrome/Edge nhận diện tên file
                base_url = f"/report/pdf/{rec.report_name}/{rec.res_id}"
                pdf_url = f"{base_url}#filename={target_filename}"

                # Nhúng iframe và ép chiều cao vừa vặn cho tài liệu chứng thư
                rec.pdf_iframe = f'<iframe src="{pdf_url}" width="100%" height="750px" style="border: none;"></iframe>'
            else:
                rec.pdf_iframe = False

    @api.model
    def open_preview(self, report_name, res_id):
        """Hàm tạo bản ghi wizard truyền tham số thô vào database"""
        wizard = self.sudo().create({
            'report_name': report_name,
            'res_id': res_id
        })

        return {
            'name': 'Print Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'fumigation.report.preview.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': self.env.context,
        }
