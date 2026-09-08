# Copyright 2026 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fumigation Certificates",
    "version": "15.0.1.2.0",
    "author": "Tuan Huynh, " "Odoo Community Association (OCA)",
    'summary': """ Manage fumigation certificates with QR and bilingual UI.""",
    'description': """
    Fumigation Certificates
    =======================
    
    Independent module to manage fumigation certificates
    for GCC / Viet Toan on Odoo 15 CE.
    """,
    "website": "https://giamdinhtoancau.com",
    "license": "AGPL-3",
    "depends": ["base", "contacts", "seenpo_multi_branch_base", "report_qr", "freight_mgmt"],
    "data": [
        'data/fumigation_data.xml',
        'data/ir_sequence_data.xml',
        'security/fumigation_security.xml',
        'security/fumigation_public_acl.xml',
        'security/ir.model.access.csv',
        "reports/report_paperformat.xml",
        'reports/fumigation_certificate_report.xml',
        'views/seenpo_fumigation_report_config_views.xml',
        'views/seenpo_fumigation_certificate_views.xml',
        'views/seenpo_fumigation_dashboard_views.xml',
        'wizard/fumigation_report_preview_wizard_views.xml'
    ],
    "assets": {
        'web.assets_backend': [
            'seenpo_gcc_fumigation/static/src/scss/seenpo_gcc_fumigation.scss'
        ]
    },
    'images': ['static/description/icon.png'],
    "installable": True,
    'application': True,
}
