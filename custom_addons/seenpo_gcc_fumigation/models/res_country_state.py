# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    fumi_cert_suffix = fields.Char(
        string='Fumigation Suffix', tracking=True,
        compute='_compute_name_change',
        store=True, readonly=False,
        default=lambda self: self._get_default_cert_suffix(),
        help="Setting suffix code for fumigation certificate, e.g. LS (for Lang Son)"
    )

    printing_name = fields.Char(
        string='Printing Name', tracking=True,
        help="Enter a custom name that will be printed in the PDF report."
    )

    active_for_fumigation = fields.Boolean(
        string='Active For Fumigation', tracking=True,
        default=False,
        help="Check this checkbox if you want this province/city displays in the province list of fumigation certificate."
    )

    def name_get(self):
        result = []
        for record in self:
            if record.fumi_cert_suffix:
                result.append((record.id, "{} ({})".format(record.name, record.fumi_cert_suffix)))
            else:
                result.append((record.id, record.name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []

        # Check if the search comes from your specific field's context
        if self._context.get('order_by_fumigation_first'):
            domain = [('name', operator, name)]
            # Fetch records matching the user's search query, ordered by active_for_fumigation DESC, then name ASC
            return self._search(
                expression.AND([domain, args]),
                order='active_for_fumigation desc',
                limit=limit,
                access_rights_uid=name_get_uid
            )

        # Standard behavior for all other views/fields
        return super(ResCountryState, self)._name_search(name, args, operator, limit, name_get_uid)

    @staticmethod
    def _get_cert_suffix_from_name(name):
        """Helper to extract uppercase first letter of each word."""
        if not name:
            return ''
        # Splits string by whitespace, grabs 1st char of each word, and uppercases it
        return ''.join([word[0].upper() for word in name.split() if word])

    @api.depends('name')
    def _compute_name_change(self):
        """Automatically updates cert_suffix whenever name changes."""
        list_cities = [
            "HO CHI MINH", "HỒ CHÍ MINH",
            "HAI PHONG", "HẢI PHÒNG",
            "DA NANG", "ĐÀ NẴNG"
            "CAN THO", "CẦN THƠ",
            "HUE", "HUẾ",
            "DONG NAI", "ĐỒNG NAI",
            "QUANG NINH", "QUẢNG NINH",
            "BAC NINH", "BẮC NINH",
            "HA NOI", "HÀ NỘI"
        ]

        for record in self:
            if record.name:
                record.fumi_cert_suffix = self._get_cert_suffix_from_name(record.name)
                is_city = record.name.lower() in (city.lower() for city in list_cities)
                if is_city:
                    record.printing_name = f"{record.name.title()} City"
                else:
                    record.printing_name = f"{record.name.title()} province"
            else:
                record.fumi_cert_suffix = ''

    def _get_default_cert_suffix(self):
        """Generates default cert_suffix if name is provided in context during record creation."""
        default_name = self._context.get('default_name')
        if default_name:
            return self._get_cert_suffix_from_name(default_name)
        return ''
