# Copyright 2018 David Juaneda - <djuaneda@sdi.es>
# Copyright 2021 Sodexis
# Copyright 2022 Tuan Huynh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Mail Activity Board",
    "summary": "Add Activity Boards",
    "version": "15.0.1.1.0",
    "development_status": "Beta",
    "category": "Social Network",
    "website": "https://odoo-community.org/",
    "author": "Tuan Huynh, Bao Thinh Ltd., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["calendar"],
    "data": ["views/mail_activity_view.xml"],
    # "assets": {
    #     "web.assets_backend": [
    #         "mail_activity_board/static/src/components/chatter_topbar/chatter_topbar.esm.js",
    #     ],
    #     "web.assets_qweb": [
    #         "mail_activity_board/static/src/components/chatter_topbar/chatter_topbar.xml",
    #     ],
    # },
}
