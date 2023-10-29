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
    'name': "Freight Management for Lang Son",
    'version': '15.0.4.1.0',
    'summary': """Create Freight Management System for branch Lang Son""",
    'description': """Create a module that allows management all freight operations (Air, Ocean, and Land).""",
    'author': 'Tuan Huynh',
    'company': 'Bao Thinh Software Ltd.',
    'maintainer': 'Bao Thinh Software Ltd.',
    'depends': ['mail', 'freight_mgmt'],
    "data": [
        "data/freight_data.xml",
        "security/freight_security.xml",
        "security/ir.model.access.csv",
        "views/freight_menu.xml",
        "views/freight_billing_views.xml",
        "views/freight_booking_views.xml",
        "views/sale_order_views.xml",
        "report/freight_billing_report.xml",
    ],
    'web.assets_frontend': [

    ],
    "assets": {
        'web.assets_backend': [

        ],
        'web.assets_qweb': [

        ]
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
