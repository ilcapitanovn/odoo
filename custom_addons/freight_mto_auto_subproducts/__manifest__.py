# -*- coding: utf-8 -*-
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
    'name': 'Freight MTO Auto PO Sub-Products',
    'version': '15.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Expand an MTO purchase line into pre-configured vendor sub-product lines',
    'description': """
Freight MTO Auto PO Sub-Products
================================
Define, on the product template (Purchase tab), a list of sub-products
(fees / vendor-side services). When a Sales Order triggers an MTO Purchase
Order for the product, the PO is automatically expanded with one line per
configured sub-product (quantity = Default Qty x quantity of the main line).
Lines with a Vendor Override go to a separate draft PO for that vendor.
Operators can still edit the generated PO freely before sending it.
    """,
    'author': 'Tuan Huynh',
    'company': 'Bao Thinh Software Ltd.',
    'maintainer': 'Bao Thinh Software Ltd.',
    'license': 'LGPL-3',
    'depends': ['freight_mgmt'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    "auto_install": False
}
