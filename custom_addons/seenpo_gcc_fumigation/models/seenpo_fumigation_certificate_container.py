# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import date
from odoo.exceptions import UserError, ValidationError
import uuid


class SeenpoFumigationCertificateContainer(models.Model):
    _name = 'seenpo.fumigation.certificate.container'
    _description = 'Fumigation Certificate Container'
    _order = 'certificate_id, sequence, id'
    _check_company_auto = True

    certificate_id = fields.Many2one('seenpo.fumigation.certificate', string='Certificate Reference',
                                     required=True, ondelete='cascade', index=True, copy=False, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    container_no = fields.Text(string='Container No.', tracking=True)
    seal_no = fields.Text(string='Seal No.', tracking=True)

    company_id = fields.Many2one(related='certificate_id.company_id', string='Company', store=True, index=True)
