# -*- coding: utf-8 -*-
{
    'name': 'Freight MTO Auto PO Sub-Products',
    'version': '15.0.1.1.1',
    'category': 'Inventory/Purchase',
    'summary': 'Expand an MTO purchase line into pre-configured vendor sub-product lines',
    'author': 'VietToanERP',
    'license': 'LGPL-3',
    'depends': ['freight_mgmt', 'sale_management', 'purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/mto_subproduct_suggest_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
