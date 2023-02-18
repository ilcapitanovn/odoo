# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Define income taxes",
    "version": "15.0.1.0.0",
    "author": "Tuan Huynh, " "Odoo Community Association (OCA)",
    "category": "Accounting",
    "website": "https://github.com/OCA/taxes",
    "license": "AGPL-3",
    "depends": ['base', 'account'],
    "data": [
        "security/ir.model.access.csv",
        "views/account_tax_income_views.xml",
    ],
    "assets": {
        'web.assets_backend': [
            'seenpo_tax_income/static/src/scss/tax_income.scss',
        ]
    },
    "installable": True,
}
