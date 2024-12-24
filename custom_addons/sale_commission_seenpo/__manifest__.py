# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sales commissions from salesman with customization",
    "version": "15.0.1.3.1",
    "author": "Tuan Huynh, " "Odoo Community Association (OCA)",
    "category": "Sales",
    "website": "https://github.com/OCA/commission",
    "license": "AGPL-3",
    "depends": ["sale_commission", "sale_commission_salesman", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/product_views.xml",
        "views/purchase_views.xml",
        "views/res_partner_views.xml",
        "views/sale_commission_views.xml",
        "views/sale_incentive_views.xml",
        "views/sale_order_views.xml"
    ],
    "assets": {
        'web.assets_backend': [
            'sale_commission_seenpo/static/src/scss/sale_commission.scss',
        ]
    },
    "installable": True,
}
