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
    'name': "Seenpo Customize Javascripts",

    'summary': """
        Contain all customize JS files or libraries from the original Odoo platform 
    """,

    'description': """
        This module contains all customize JS files or libraries from the original odoo platform.
        If there is any problems in JS files from original Odoo platform, it should be fixed here.
        Steps:
        - Clone the original file into here
        - Then making changes
        - Deploy changes
    """,

    'author': "Tuan Huynh",
    'company': 'Bao Thinh Software Ltd.',
    'maintainer': 'Bao Thinh Software Ltd.',
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical',
    'version': '15.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    'assets': {
        'web.assets_backend': [
            '/seenpo_custom_javascripts/static/lib/luxon/luxon.js',
        ],
        'web.assets_common': [
            '/seenpo_custom_javascripts/static/lib/luxon/luxon.js',
        ],
    },

    # always loaded
    'data': [],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': False,
}
