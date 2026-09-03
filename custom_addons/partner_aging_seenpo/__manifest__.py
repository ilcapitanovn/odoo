# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Interactive Partner Aging at any date",
    "version": "15.0.1.0.0",
    "author": "Tuan Huynh, " "Odoo Community Association (OCA)",
    'summary': """ An extension module to customize updates for the original
                 module partner_aging.""",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["partner_aging", "base_accounting_kit"],
    "data": [
        "views/res_partner_aging_payable_views.xml",
        "views/res_partner_aging_receivable_views.xml"
    ],
    "installable": True,
}
