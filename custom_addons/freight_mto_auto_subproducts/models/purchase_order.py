# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_mto_sub_po = fields.Boolean(
        string='Auto Sub-Products PO', readonly=True, copy=False,
        help="Generated automatically to hold MTO sub-products for a vendor "
             "different from the vendor of the main PO.")

    def _mto_get_or_create_vendor_po(self, vendor):
        """Return a draft 'sub-products' PO for ``vendor`` sharing the origin
        (and company) of ``self``; create it if needed."""
        self.ensure_one()
        PO = self.env['purchase.order'].sudo().with_company(self.company_id)
        domain = [
            ('is_mto_sub_po', '=', True),
            ('state', '=', 'draft'),
            ('partner_id', '=', vendor.id),
            ('company_id', '=', self.company_id.id),
            ('origin', '=', self.origin or False),
        ]
        po = PO.search(domain, limit=1)
        if po:
            return po
        company = self.company_id
        fpos = self.env['account.fiscal.position'].sudo().with_company(
            company).get_fiscal_position(vendor.id)
        return PO.create({
            'partner_id': vendor.id,
            'company_id': company.id,
            'origin': self.origin,
            'currency_id': (vendor.with_company(company).property_purchase_currency_id.id
                            or company.currency_id.id),
            'payment_term_id': vendor.with_company(
                company).property_supplier_payment_term_id.id,
            'fiscal_position_id': fpos,
            'picking_type_id': self.picking_type_id.id,
            'user_id': self.user_id.id,
            'date_order': fields.Datetime.now(),
            'is_mto_sub_po': True,
        })
