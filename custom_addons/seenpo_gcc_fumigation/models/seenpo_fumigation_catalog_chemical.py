# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SeenpoFumigationCatalogChemical(models.Model):
    _name = "seenpo.fumigation.catalog.chemical"
    _description = "Seenpo Fumigation Catalog Chemical"

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Char(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('fumi_code_uniq', 'unique(code)', 'The chemical code must be unique!')
    ]

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.code + " - " + rec.name))
        return result
