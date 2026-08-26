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
        # Which records will end up being an agent *after* this write —
        # computed with filtered(), which works on any recordset size
        # (unlike self.agent, which requires exactly one record).
        if 'agent' in vals:
            will_be_agent = self if vals['agent'] else self.browse()
        else:
            will_be_agent = self.filtered('agent')

        # Snapshot, before the write, which of those still need the
        # self-link (i.e. don't already have agent_ids set).
        partners_needing_self_link = will_be_agent.filtered(lambda p: not p.agent_ids)

        res = super(ResPartner, self).write(vals)

        # Only auto-default agent_ids when the caller isn't already setting
        # it explicitly in this same write. Looped per-record on purpose:
        # each partner must link to *itself*, which a single shared vals
        # dict can't express for a batched multi-record write.
        if 'agent_ids' not in vals:
            for partner in partners_needing_self_link:
                partner.agent_ids = [(6, 0, partner.ids)]

        return res
