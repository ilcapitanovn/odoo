# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.mto_subproduct_suggest import name_tokens, similarity


@tagged('post_install', '-at_install')
class TestSuggestSubproducts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env['product.product']
        Partner = cls.env['res.partner']
        cls.main_vendor = Partner.create({'name': 'Main Vendor'})
        cls.port_vendor = Partner.create({'name': 'Port Authority'})
        cls.prod_a = Product.create({
            'name': 'Entrusted Export Service, Banana, HCM - SHA, JJ ,HNT',
            'type': 'service'})
        cls.prod_b = Product.create({'name': 'DOC - SJJ', 'type': 'service'})
        cls.prod_c = Product.create({'name': 'THC - 40RH, SJJ', 'type': 'service'})
        cls.prod_d = Product.create({'name': 'SEAL - SJJ', 'type': 'service'})

    def _booking(self, origin, a_qty, lines):
        """Confirmed history: PO of A (main vendor) + POs for other vendors."""
        PO = self.env['purchase.order']
        po = PO.create({'partner_id': self.main_vendor.id, 'origin': origin})
        self._add_line(po, self.prod_a, a_qty)
        po.state = 'purchase'
        for product, qty, vendor in lines:
            po2 = PO.create({'partner_id': vendor.id, 'origin': origin})
            self._add_line(po2, product, qty)
            po2.state = 'purchase'

    def _add_line(self, po, product, qty):
        self.env['purchase.order.line'].create({
            'order_id': po.id, 'product_id': product.id, 'name': product.name,
            'product_qty': qty, 'product_uom': product.uom_po_id.id,
            'price_unit': 1.0, 'date_planned': '2026-01-01 00:00:00'})

    def _wizard(self):
        wiz = self.env['mto.subproduct.suggest.wizard'].create(
            {'template_id': self.prod_a.product_tmpl_id.id})
        wiz._populate()
        return wiz

    def test_tokens_and_similarity(self):
        self.assertEqual(name_tokens('Hồ Chí Minh - SHA, J'), {'HO', 'CHI', 'MINH', 'SHA'})
        self.assertGreater(similarity(
            'Entrusted Export Service, Banana, HCM - SHA, JJ ,HNT',
            'Entrusted Export Service, Apple, HCM - SHA, JJ, HNT'), 0.6)
        self.assertEqual(similarity('', 'abc'), 0.0)

    def test_history_suggestions(self):
        # B in all 3 bookings (main vendor), C in 1 booking (other vendor)
        self._booking('S001', 2, [(self.prod_b, 2, self.main_vendor),
                                  (self.prod_c, 4, self.port_vendor)])
        self._booking('S002', 1, [(self.prod_b, 1, self.main_vendor)])
        self._booking('S003', 1, [(self.prod_b, 1, self.main_vendor)])
        wiz = self._wizard()
        lines = {l.sub_product_id: l for l in wiz.line_ids}
        self.assertEqual(set(lines), {self.prod_b, self.prod_c})
        line_b, line_c = lines[self.prod_b], lines[self.prod_c]
        self.assertTrue(line_b.selected)           # 3/3 >= 50%
        self.assertFalse(line_c.selected)          # 1/3 < 50%
        self.assertEqual(line_b.qty, 1.0)
        self.assertFalse(line_b.vendor_id)         # same vendor as the main PO
        self.assertEqual(line_c.vendor_id, self.port_vendor)
        self.assertEqual(line_c.qty, 2.0)          # 4 per 2 units of A
        self.assertEqual(line_b.source, 'history')

    def test_similar_product_fallback_and_confirm(self):
        other = self.env['product.product'].create({
            'name': 'Entrusted Export Service, Apple, HCM - SHA, JJ, HNT',
            'type': 'service'})
        Cfg = self.env['product.template.mto.subproduct']
        Cfg.create({'template_id': other.product_tmpl_id.id,
                    'sub_product_id': self.prod_b.id, 'qty': 1.0})
        Cfg.create({'template_id': other.product_tmpl_id.id,
                    'sub_product_id': self.prod_d.id, 'qty': 3.0,
                    'vendor_id': self.port_vendor.id})
        wiz = self._wizard()
        self.assertEqual(wiz.source_template_id, other.product_tmpl_id)
        self.assertEqual(wiz.line_ids.mapped('source'), ['similar', 'similar'])
        wiz.action_confirm()
        cfgs = self.prod_a.product_tmpl_id.mto_subproduct_ids
        self.assertEqual(cfgs.mapped('sub_product_id'), self.prod_b | self.prod_d)
        self.assertEqual(cfgs.filtered(
            lambda c: c.sub_product_id == self.prod_d).qty, 3.0)
        # nothing new to suggest for the same product afterwards
        self.assertFalse(self._wizard().line_ids)

    def test_cap_includes_existing_lines(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'freight_mto_auto_subproducts.suggest_max', '2')
        self.env['product.template.mto.subproduct'].create({
            'template_id': self.prod_a.product_tmpl_id.id,
            'sub_product_id': self.prod_d.id})
        self._booking('S010', 1, [(self.prod_b, 1, self.main_vendor),
                                  (self.prod_c, 1, self.main_vendor)])
        wiz = self._wizard()
        self.assertEqual(wiz.free_slots, 1)
        self.assertEqual(len(wiz.line_ids), 1)      # trimmed to free slots
        wiz.line_ids.write({'selected': True})
        # forcing an extra line must be refused
        wiz.write({'line_ids': [(0, 0, {
            'source': 'history', 'sub_product_id': self.prod_c.id,
            'qty': 1.0, 'selected': True})]})
        with self.assertRaises(UserError):
            wiz.action_confirm()
