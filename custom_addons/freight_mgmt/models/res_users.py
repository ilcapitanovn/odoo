# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    """inherited res users"""
    _inherit = "res.users"

    @api.model
    def create(self, vals):
        """
        Else the menu will be still hidden even after removing from the list
        """
        self.clear_caches()
        return super(ResUsers, self).create(vals)

    def write(self, vals):
        """
        Else the menu will be still hidden even after removing from the list.
        Skip the Admin user from menu hidden, else once the menu is hidden, it will be difficult to re-enable it.
        """
        res = super(ResUsers, self).write(vals)

        try:
            if self.id != self.env.ref('base.user_admin').id:
                menu_freight_main = self.env.ref('freight_mgmt.freight_mgmt_main_menu', False)
                branch_saigon = self.env.ref('seenpo_multi_branch_base.seenpo_branch_saigon', False)
                if menu_freight_main and branch_saigon and self.branch_ids:
                    if branch_saigon.id not in self.branch_ids.ids:
                        menu_freight_main.write({
                            'restrict_user_ids': [(4, self.id)]
                        })
                    else:       # Remove user restriction if it is in allowed branches
                        menu_freight_main.write({
                            'restrict_user_ids': [(3, self.id)]
                        })
                    self.clear_caches()
        except AccessError as e:
            print("AccessError occurred when write restrict user access to Freight menu: ", str(e))

        return res
