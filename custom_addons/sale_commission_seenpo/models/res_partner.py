# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    target_sales = fields.Float(string="Sales Target")
    incentive_id = fields.Many2one(
        string="Incentive",
        comodel_name="sale.incentive",
        help="This is the default incentive used for the salesman where this incentive is assigned."
    )

    def write(self, vals):
        if 'agent' in vals:
            is_agent = vals['agent']
        else:
            is_agent = self.agent

        if is_agent and not ('agent_ids' in vals) and not self.agent_ids:
            vals['agent_ids'] = [(6, 0, self.ids)]

        res = super(ResPartner, self).write(vals)
        return res