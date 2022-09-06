# Copyright 2008-2016 Camptocamp
# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2020 CorporateHub (https://corporatehub.eu)
# Copyright 2022 Bao Thinh Software Ltd. (https://baothinh.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Currency Rate Update",
    "version": "15.0.1.1.0",
    "author": "Tuan Huynh, Bao Thinh Software Ltd., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/currency",
    "license": "AGPL-3",
    "category": "Financial Management/Configuration",
    "summary": "Update exchange rates using OCA modules",
    "depends": ["base", "mail", "account"],
    "data": [
        "data/cron.xml",
        "security/ir.model.access.csv",
        "security/res_currency_rate_provider.xml",
        "views/res_currency_rate.xml",
        "views/res_currency_rate_provider.xml",
        "views/res_config_settings.xml",
        "wizards/res_currency_rate_update_wizard.xml",
    ],
    "installable": True,
}
