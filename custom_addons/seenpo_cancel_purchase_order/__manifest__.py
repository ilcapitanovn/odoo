# -*- coding: utf-8 -*-
{
    'name': 'Seenpo Cancel Purchase Order',
    'summary': "Seenpo Cancel Purchase Order",
    'description': "Seenpo Cancel Purchase Order",

    'author': "Tuan Huynh, " "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/',
    'support': 'baothinhstore@gmail.com',

    'category': 'Purchases',
    'version': '15.0.0.1.0',
    'depends': ['purchase'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_order_cancel.xml',
        'views/purchase_views.xml',
    ],

    'license': "OPL-1",
    'auto_install': False,
    'installable': True,

    'images': ['static/description/banner.png'],
    'pre_init_hook': 'pre_init_check',
}
