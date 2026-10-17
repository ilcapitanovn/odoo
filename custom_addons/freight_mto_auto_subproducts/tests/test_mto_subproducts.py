# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMtoSubproducts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env['res.partner']
        Product = cls.env['product.product']
        cls.vendor_main = Partner.create({'name': 'Main Vendor'})
        cls.vendor_port = Partner.create({'name': 'Port Authority'})
        cls.prod_a = Product.create({'name': 'Entrusted Goods (A)', 'type': 'service'})
        cls.prod_b = Product.create({'name': 'Customs Declaration', 'type': 'service'})
        cls.prod_c = Product.create({'name': 'Terminal Handling Fee', 'type': 'service'})
        cls.env['product.supplierinfo'].create({
            'name': cls.vendor_port.id,
            'product_tmpl_id': cls.prod_c.product_tmpl_id.id,
            'price': 50.0,
        })
        Cfg = cls.env['product.template.mto.subproduct']
        cls.cfg_b = Cfg.create({
            'template_id': cls.prod_a.product_tmpl_id.id,
            'sub_product_id': cls.prod_b.id, 'qty': 1.0, 'sequence': 1})
        cls.cfg_c = Cfg.create({
            'template_id': cls.prod_a.product_tmpl_id.id,
            'sub_product_id': cls.prod_c.id, 'qty': 2.0, 'sequence': 2,
            'vendor_id': cls.vendor_port.id})

    def _make_po_line(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor_main.id, 'origin': 'S00001'})
        line = self.env['purchase.order.line'].with_context(
            mto_expand_subproducts=True).create({
                'order_id': po.id,
                'product_id': self.prod_a.id,
                'name': self.prod_a.name,
                'product_qty': 3.0,
                'product_uom': self.prod_a.uom_po_id.id,
                'price_unit': 100.0,
                'date_planned': '2026-01-01 00:00:00',
            })
        return po, line

    def test_expansion_and_vendor_split(self):
        po, line = self._make_po_line()
        # B (no vendor override) on the main PO, A + B
        self.assertEqual(len(po.order_line), 2)
        sub_b = po.order_line.filtered('is_mto_auto_line')
        self.assertEqual(sub_b.product_id, self.prod_b)
        self.assertEqual(sub_b.product_qty, 3.0)
        self.assertEqual(sub_b.mto_parent_line_id, line)
        # C has a vendor override -> separate draft PO, qty 2 x 3 = 6
        sub_po = self.env['purchase.order'].search([
            ('is_mto_sub_po', '=', True), ('partner_id', '=', self.vendor_port.id)])
        self.assertEqual(len(sub_po), 1)
        self.assertEqual(sub_po.origin, 'S00001')
        self.assertEqual(sub_po.order_line.product_qty, 6.0)
        self.assertEqual(sub_po.order_line.price_unit, 50.0)

    def test_no_expansion_without_flag(self):
        po = self.env['purchase.order'].create({'partner_id': self.vendor_main.id})
        self.env['purchase.order.line'].create({
            'order_id': po.id, 'product_id': self.prod_a.id,
            'name': 'A', 'product_qty': 1.0,
            'product_uom': self.prod_a.uom_po_id.id, 'price_unit': 1.0,
            'date_planned': '2026-01-01 00:00:00'})
        self.assertEqual(len(po.order_line), 1)

    def test_merge_increases_sub_lines(self):
        po, line = self._make_po_line()
        line.with_context(mto_expand_subproducts=True).write({'product_qty': 5.0})
        sub_b = po.order_line.filtered('is_mto_auto_line')
        self.assertEqual(sub_b.product_qty, 5.0)

    def test_no_nesting(self):
        with self.assertRaises(ValidationError):
            self.env['product.template.mto.subproduct'].create({
                'template_id': self.prod_b.product_tmpl_id.id,
                'sub_product_id': self.prod_c.id})
        with self.assertRaises(ValidationError):
            self.env['product.template.mto.subproduct'].create({
                'template_id': self.prod_a.product_tmpl_id.id,
                'sub_product_id': self.prod_a.id})
