from odoo import _, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    is_activities_completed_search = fields.Boolean(compute="_compute_is_activities_completed_search",
                                                    search="_search_is_activities_completed_search")

    def _compute_is_activities_completed_search(self):
        for rec in self:
            rec.is_activities_completed_search = False

    def _search_is_activities_completed_search(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)

        open_activities = self.env['mail.activity'].with_context(active_test=False).search([
            ('res_model', '=', 'res.partner'), ('active', '=', True)])
        open_res_ids = [o.res_id for o in open_activities]
        completed_activities = self.env['mail.activity'].with_context(active_test=False).search([
            ('res_model', '=', 'res.partner'), ('active', '=', False), ('done', '=', True),
            ('res_id', 'not in', open_res_ids)])
        res_ids = [o.res_id for o in completed_activities]
        deduplicated_red_ids = list(set(res_ids))
        return [('id', 'in', deduplicated_red_ids)]
