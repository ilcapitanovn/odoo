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
    'version': '15.0.1.0.0',
    'summary': """Create Freight Management System""",
    'description': """Create a module that allows management all freight operations (Air, Ocean, and Land).""",
    'author': 'Tuan Huynh',
    'company': 'Bao Thinh Software Ltd.',
    'maintainer': 'Bao Thinh Software Ltd.',
    'depends': ['mail', 'sale', 'sale_margin', 'portal', 'base'],
    "data": [
        "data/freight_data.xml",
        "data/freight_demo.xml",
        "security/freight_security.xml",
        "security/ir.model.access.csv",
        "views/freight_booking_views.xml",
        "views/freight_billing_views.xml",
        "views/freight_catalog_airline_views.xml",
        "views/freight_catalog_container_views.xml",
        "views/freight_catalog_incoterm_views.xml",
        "views/freight_catalog_port_views.xml",
        "views/freight_catalog_stage_views.xml",
        "views/freight_catalog_vessel_views.xml",
        "views/freight_menu.xml",
        "views/billing_portal_template.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "report/report_paperformat.xml",
        "report/freight_billing_report.xml"
    ],
    'web.assets_frontend': [
        'sale/static/src/scss/sale_portal.scss',
        'sale/static/src/js/sale_portal_sidebar.js'
    ],
    "assets": {
        'web.assets_backend': [
            'freight_mgmt/static/src/scss/freight_mgmt.scss',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
