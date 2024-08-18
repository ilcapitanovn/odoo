# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    """inherited res users"""
    _inherit = "res.users"

    def write(self, vals):
        """
        Else the menu will be still hidden even after removing from the list.
        Skip the Admin user from menu hidden, else once the menu is hidden, it will be difficult to re-enable it.
        """
        res = super(ResUsers, self).write(vals)

        try:
            if self.id != self.env.ref('base.user_admin').id:
                menu_freight_main = self.env.ref('freight_trading_mgmt.freight_trading_mgmt_main_menu', False)
                branch_trading = self.env.ref('seenpo_multi_branch_base.seenpo_branch_trading', False)
                if menu_freight_main and branch_trading and self.branch_ids:
                    if branch_trading.id not in self.branch_ids.ids:
                        menu_freight_main.write({
                            'restrict_user_ids': [(4, self.id)]
                        })
                    else:  # Remove user restriction if it is in allowed branches
                        menu_freight_main.write({
                            'restrict_user_ids': [(3, self.id)]
                        })
                    self.clear_caches()
        except AccessError as e:
            print("AccessError occurred when write restrict user access to Trading (Freight) menu: ", str(e))

        return res
