# -*- coding: utf-8 -*-
#############################################################################
#
#    Bao Thinh Software Ltd.
#
#    Copyright (C) 2022-TODAY Bao Thinh Software(<https://www.baothinh.com>)
#    Author: Bao Thinh Software(<https://www.baothinh.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Freight Management",
    'version': '15.0.5.4.5',
    'summary': """Create Freight Management System""",
    'description': """Create a module that allows management all freight operations (Air, Ocean, and Land).""",
    'author': 'Tuan Huynh',
    'company': 'Bao Thinh Software Ltd.',
    'maintainer': 'Bao Thinh Software Ltd.',
    'depends': ['mail', 'sale', 'sale_margin', 'portal', 'base', 'sale_purchase', 'website_slides',
                'account', 'sale_commission_seenpo', 'seenpo_multi_branch_base'],
    "data": [
        "data/freight_data.xml",
        "data/freight_demo.xml",
        "data/freight_email_templates.xml",
        "security/freight_security.xml",
        "security/ir.model.access.csv",
        "views/freight_booking_views.xml",
        "views/freight_billing_views.xml",
        "views/freight_debit_note_views.xml",
        "views/freight_credit_note_views.xml",
        "views/freight_catalog_airline_views.xml",
        "views/freight_catalog_container_views.xml",
        "views/freight_catalog_incoterm_views.xml",
        "views/freight_catalog_port_views.xml",
        "views/freight_catalog_stage_views.xml",
        "views/freight_catalog_vehicle_supplier_views.xml",
        "views/freight_catalog_vessel_views.xml",
        "views/freight_form_wo_views.xml",
        "views/freight_menu.xml",
        "views/billing_portal_template.xml",
        "views/crm_lead_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/product_views.xml",
        "views/product_pricelist_views.xml",
        "views/purchase_views.xml",
        "views/hr_employee_views.xml",
        "views/restrict_menu_views.xml",
        'views/sale_portal_templates.xml',
        "views/website_slides_views.xml",
        "report/report_paperformat.xml",
        "report/freight_billing_report.xml",
        "report/freight_delivery_order_report.xml",
        "report/freight_arrival_notice_report.xml",
        "report/freight_form_wo_report.xml",
        "report/freight_sale_incentive_report_template.xml",
        "report/sale_profit_forwarder_analysis_report_view.xml",
        "report/sale_incentive_analysis_report_view.xml",
        "report/sale_report_templates.xml",
        "wizard/wizard_incentive_report.xml"
    ],
    'web.assets_frontend': [
        'sale/static/src/scss/sale_portal.scss',
        'sale/static/src/js/sale_portal_sidebar.js'
    ],
    "assets": {
        'web.assets_backend': [
            'freight_mgmt/static/src/scss/freight_mgmt.scss',
            'freight_mgmt/static/src/js/button_booking_sheet.js'
        ],
        'web.assets_qweb': [
            'freight_mgmt/static/src/xml/button_booking_sheet.xml'
        ]
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
