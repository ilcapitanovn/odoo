# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.mto_subproduct_suggest import normalize, token_list


@tagged('post_install', '-at_install')
class TestSuggestSubproducts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env['product.product']
        cls.prod_a = Product.create({
            'name': 'Entrusted Export Service, Banana, HCM - SHA, JJ ,HNT',
            'type': 'service'})
        mk = lambda name: Product.create({'name': name, 'type': 'service'})
        cls.of_ = mk('OF, VNHCM - CNSHA, 40RH, SJJ')
        cls.doc = mk('DOC - SJJ')
        cls.truck = mk('TRUCKING, 40RH, BAO AN - BAI PHUONG DONG, HNT')
        cls.other_lane = mk('OF, VNHCM - CNNSS, 40HC, YML')
        cls.other_main = mk('Entrusted Export Service, Apple, HCM - SHA, JJ, HNT')
        cls.unrelated = mk('Office Chair Zzq')
        cls.main_vendor = cls.env['res.partner'].create({'name': 'Main Vendor'})
        cls.port_vendor = cls.env['res.partner'].create({'name': 'Port Authority'})

    def _wizard(self):
        wiz = self.env['mto.subproduct.suggest.wizard'].create(
            {'template_id': self.prod_a.product_tmpl_id.id})
        wiz._populate()
        return wiz

    def _products(self, wiz):
        return {l.sub_product_id: l for l in wiz.line_ids}

    # ---------------------------------------------------------- helpers
    def test_tokens(self):
        self.assertEqual(
            [n for _r, n in token_list('Hồ Chí Minh - SHA, J')],
            ['HO', 'CHI', 'MINH', 'SHA'])
        self.assertEqual(normalize('Đường'), 'DUONG')

    # ------------------------------------------------- similarity mode
    def test_default_mode_and_keywords(self):
        wiz = self._wizard()
        self.assertEqual(wiz.mode, 'similar')
        self.assertEqual(wiz.keywords.split(), ['Banana', 'HCM', 'SHA', 'JJ', 'HNT'])
        self.assertTrue(wiz.ignore_word_ids)

    def test_similarity_ranking_and_main_like_products_hidden(self):
        wiz = self._wizard()
        lines = self._products(wiz)
        self.assertNotIn(self.unrelated, lines)
        self.assertNotIn(self.other_main, lines)       # contains ignored phrase
        self.assertEqual(wiz.line_ids[0].sub_product_id, self.of_)   # HCM+SHA+JJ
        self.assertTrue(lines[self.of_].selected)
        self.assertFalse(lines[self.doc].selected)                   # JJ only
        self.assertIn(self.truck, lines)
        self.assertIn('Banana', wiz.info)                            # no match

    def test_ignore_word_added_by_user(self):
        wiz = self._wizard()
        self.assertIn(self.doc, self._products(wiz))
        word = self.env['mto.subproduct.ignore.word'].create({'name': 'JJ'})
        wiz.ignore_word_ids = [(4, word.id)]
        wiz.action_reload()
        self.assertNotIn(self.doc, self._products(wiz))   # only matched on JJ
        self.assertIn(self.truck, self._products(wiz))    # HNT still matches

    def test_vendor_name_match_and_override(self):
        Partner = self.env['res.partner']
        main_vendor = Partner.create({'name': 'Jiaxiang Lines'})
        cand_vendor = Partner.create({'name': 'Jiaxiang Terminal Co'})
        fee = self.env['product.product'].create(
            {'name': 'Fuel Surcharge', 'type': 'service'})
        Supplier = self.env['product.supplierinfo']
        Supplier.create({'name': main_vendor.id, 'price': 1.0,
                         'product_tmpl_id': self.prod_a.product_tmpl_id.id})
        Supplier.create({'name': cand_vendor.id, 'price': 1.0,
                         'product_tmpl_id': fee.product_tmpl_id.id})
        wiz = self._wizard()
        self.assertEqual(wiz.vendor_ids, main_vendor)
        wiz.keywords = 'HCM Jiaxiang'
        wiz.action_reload()
        lines = self._products(wiz)
        self.assertIn(fee, lines)                       # matched on vendor name
        self.assertEqual(lines[fee].vendor_id, cand_vendor)

    def test_same_vendor_as_main_needs_no_override(self):
        Supplier = self.env['product.supplierinfo']
        Supplier.create({'name': self.port_vendor.id, 'price': 1.0,
                         'product_tmpl_id': self.prod_a.product_tmpl_id.id})
        Supplier.create({'name': self.port_vendor.id, 'price': 1.0,
                         'product_tmpl_id': self.doc.product_tmpl_id.id})
        line = self._wizard().line_ids.filtered(
            lambda l: l.sub_product_id == self.doc)
        self.assertFalse(line.vendor_id)
        self.assertTrue(line.selected)                  # favoured vendor

    # ------------------------------------------------------ history mode
    def _booking(self, origin, a_qty, lines):
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

    def test_history_mode(self):
        self._booking('S001', 2, [(self.doc, 2, self.main_vendor),
                                  (self.of_, 4, self.port_vendor)])
        self._booking('S002', 1, [(self.doc, 1, self.main_vendor)])
        self._booking('S003', 1, [(self.doc, 1, self.main_vendor)])
        wiz = self._wizard()
        wiz.mode = 'history'
        wiz.action_reload()
        lines = self._products(wiz)
        self.assertEqual(set(lines), {self.doc, self.of_})
        self.assertTrue(lines[self.doc].selected)        # 3/3
        self.assertFalse(lines[self.of_].selected)       # 1/3
        self.assertEqual(lines[self.doc].qty, 1.0)
        self.assertFalse(lines[self.doc].vendor_id)
        self.assertEqual(lines[self.of_].vendor_id, self.port_vendor)
        self.assertEqual(lines[self.of_].qty, 2.0)       # 4 per 2 units of A

    def test_history_mode_without_history_has_no_fallback(self):
        wiz = self._wizard()
        wiz.mode = 'history'
        wiz.action_reload()
        self.assertFalse(wiz.line_ids)
        self.assertIn('No purchase history', wiz.info)

    def test_switch_back_to_similarity(self):
        wiz = self._wizard()
        wiz.mode = 'history'
        wiz.action_reload()
        self.assertFalse(wiz.line_ids)
        wiz.mode = 'similar'
        wiz.action_reload()
        self.assertIn(self.of_, self._products(wiz))

    # ------------------------------------------------------------ confirm
    def test_confirm_and_skip_existing(self):
        wiz = self._wizard()
        wiz.line_ids.write({'selected': False})
        wiz.line_ids.filtered(lambda l: l.sub_product_id == self.of_).selected = True
        wiz.action_confirm()
        cfgs = self.prod_a.product_tmpl_id.mto_subproduct_ids
        self.assertEqual(cfgs.mapped('sub_product_id'), self.of_)
        self.assertNotIn(self.of_, self._products(self._wizard()))

    def test_cap_includes_existing_lines(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'freight_mto_auto_subproducts.suggest_max', '2')
        self.env['product.template.mto.subproduct'].create({
            'template_id': self.prod_a.product_tmpl_id.id,
            'sub_product_id': self.unrelated.id})
        wiz = self._wizard()
        self.assertEqual(wiz.free_slots, 1)
        self.assertEqual(len(wiz.line_ids), 1)          # trimmed to free slots
        wiz.write({'line_ids': [(0, 0, {
            'sub_product_id': self.doc.id, 'qty': 1.0, 'selected': True})]})
        wiz.line_ids.write({'selected': True})
        with self.assertRaises(UserError):
            wiz.action_confirm()
