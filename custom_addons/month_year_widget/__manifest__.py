# -*- coding: utf-8 -*-
{
    'name': "Seenpo Month and Year Widget Field",
    'summary': """ Month and Year Selection for Odoo 15 Community Edition. """,
    'description': """ Sometimes you don't really need to enter a specific day for a date in Odoo,
    probably you just need to know the month and the year. For cases like this, with this new widget 
    you don't have to care about entering a random number for the day.
    
    Usage:
    
    Once the module is installed. Add it to the __manifest__.py of the module where you want to use it.
    Then, in the xml add the widget='month_year_format'.
    """,
    'author': "Tuan Huynh",
    'website': "https://baothinh.com",
    'category': 'Technical',
    'version': '15.0.1.0.0',
    'license': "AGPL-3",
    'depends': ['web'],
    'data': [
        'views/assets.xml'
    ],
    "assets": {
        'web.assets_backend': [
            'month_year_widget/static/src/js/month_year_format_widget.js'
        ],
        'web.assets_common': [
            'month_year_widget/static/lib/tempusdominus.js',
        ]
    }
}
