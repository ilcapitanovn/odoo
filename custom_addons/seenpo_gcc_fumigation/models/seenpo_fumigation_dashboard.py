# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import date


class FumigationDashboard(models.Model):
    _name = 'seenpo.fumigation.dashboard'
    _description = 'Fumigation Dashboard'
    _rec_name = 'name'

    name = fields.Char(default='Fumigation Dashboard')

    month_filter = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', default=lambda self: str(date.today().month).zfill(2))

    certificate_count = fields.Integer(string='Certificates Issued', compute='_compute_stats')
    container_count = fields.Integer(string='Container / Cont', compute='_compute_stats')
    sea_count = fields.Integer(string='Sea Route', compute='_compute_stats')
    road_count = fields.Integer(string='Road Route', compute='_compute_stats')
    pallet_count = fields.Integer(string='Wooden Pallet', compute='_compute_stats')
    air_count = fields.Integer(string='Air Route', compute='_compute_stats')

    certificate_ids = fields.Many2many(
        'seenpo.fumigation.certificate',
        string='Certificates in Month',
        compute='_compute_stats'
    )

    @api.depends('month_filter')
    def _compute_stats(self):
        for rec in self:
            # lọc theo tháng fumigation_date (hoặc create_date tùy bạn)
            month = rec.month_filter
            certificates = self.env['seenpo.fumigation.certificate'].search([
                ('fumigation_date', 'like', f"%-{month}-%")
            ])

            rec.certificate_count = len(certificates)
            rec.container_count = len(certificates.filtered(lambda c: c.container_no))
            rec.sea_count = len(certificates.filtered(lambda c: c.transport_type == 'sea'))
            rec.road_count = len(certificates.filtered(lambda c: c.transport_type == 'road'))
            rec.pallet_count = len(certificates.filtered(lambda c: c.transport_type == 'pallet'))
            rec.air_count = len(certificates.filtered(lambda c: c.transport_type == 'air'))
            rec.certificate_ids = [(6, 0, certificates.ids)]
