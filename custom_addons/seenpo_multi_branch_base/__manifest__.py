# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Việt Toản Multi Branch Operations",
    "version": "15.0.0.2.0",
    "summary": """ Multiple Branch Unit Operation Setup for All 
                   Modules In Odoo""",
    "description": """Multiple Branch Unit Operation Setup for All 
                      Modules In Odoo, Branch, Branch Operations, 
                      Multiple Branch, Branch Setup""",
    "author": "Tuan Huynh, " "Odoo Community Association (OCA)",
    "category": 'Tools',
    "website": "https://www.baothinh.com/",
    "license": "AGPL-3",
    "depends": ['base', 'sale_management', 'sale_stock', 'purchase_stock', 'stock_account'],
    "data": [
        "data/seenpo_multi_branch_data.xml",
        "security/multi_branch_base_security.xml",
        "security/ir.model.access.csv",
        "views/res_branch_views.xml",
        "views/branch_res_partner_views.xml",
        "views/branch_res_users_views.xml",
        "views/branch_sale_order_views.xml",
        "views/branch_purchase_order_views.xml",
        "views/branch_account_move_views.xml"
    ],
    "assets": {
        'web.assets_backend': [
            'seenpo_multi_branch_base/static/src/scss/seenpo_multi_branch_base.scss'
        ]
    },
    "installable": True,
    'application': True,
}
