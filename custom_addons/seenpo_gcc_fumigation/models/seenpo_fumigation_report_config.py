# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SeenpoFumigationReportConfig(models.TransientModel):
    _name = 'seenpo.fumigation.report.config'
    _description = 'GCC Fumigation Report Configuration'

    seenpo_fumigation_header_font_size = fields.Char(
        string='Header Font Size', default='15',
        help="At section 'GLOBAL CARGO CONTROL CO., LTD'. Input font-size format by px (e.g., 15, 18, 20)")
    seenpo_fumigation_title_font_size = fields.Char(
        string='Title Font Size', default='28',
        help="For the text 'Certificate of Fumigation'. Input font-size format by px (e.g., 28, 30)")
    seenpo_fumigation_content_font_size = fields.Char(
        string='Content Font Size', default='16',
        help="Start from 'Certilicate No.'. Input font-size format by px (e.g., 16, 20)")
    seenpo_fumigation_signature_font_size = fields.Char(
        string='Signature Font Size', default='18',
        help="'HO CHI MINH City, date'. Input font-size format by px (e.g., 18, 20)")

    @api.model
    def default_get(self, fields_list):
        """Khi mở form, lấy dữ liệu từ ir.config_parameter lên giao diện"""
        res = super(SeenpoFumigationReportConfig, self).default_get(fields_list)
        param_obj = self.env['ir.config_parameter'].sudo()

        res.update({
            'seenpo_fumigation_header_font_size': param_obj.get_param('seenpo_gcc_fumigation.header_font_size', '15'),
            'seenpo_fumigation_title_font_size': param_obj.get_param('seenpo_gcc_fumigation.title_font_size', '28'),
            'seenpo_fumigation_content_font_size': param_obj.get_param('seenpo_gcc_fumigation.content_font_size', '16'),
            'seenpo_fumigation_signature_font_size': param_obj.get_param('seenpo_gcc_fumigation.signature_font_size', '18')
        })
        return res

    def execute(self):
        """Khi bấm nút Save trên form, lưu dữ liệu xuống ir.config_parameter"""
        self.ensure_one()
        param_obj = self.env['ir.config_parameter'].sudo()

        param_obj.set_param('seenpo_gcc_fumigation.header_font_size', self.seenpo_fumigation_header_font_size or '15')
        param_obj.set_param('seenpo_gcc_fumigation.title_font_size', self.seenpo_fumigation_title_font_size or '28')
        param_obj.set_param('seenpo_gcc_fumigation.content_font_size', self.seenpo_fumigation_content_font_size or '16')
        param_obj.set_param('seenpo_gcc_fumigation.signature_font_size', self.seenpo_fumigation_signature_font_size or '18')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Configuration saved successfully.',
                'type': 'success',
                'sticky': False,
            }
        }
