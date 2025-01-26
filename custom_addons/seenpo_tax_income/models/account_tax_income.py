# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTaxIncome(models.Model):
    _name = "account.tax.income"
    _description = "Income taxes in Account"

    def _get_default_currency_id(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')])
        if vnd:
            return vnd.id
        return self.env.company.currency_id.id

    name = fields.Char("Name", required=True)
    section_ids = fields.One2many(
        string="Sections",
        comodel_name="account.tax.income.section",
        inverse_name="tax_id",
    )

    active = fields.Boolean(default=True)
    tax_income_type = fields.Selection(
        selection=[("fixed", "Fixed Percentage"), ("section", "By Sections")],
        string="Tax Type",
        required=True,
        default="fixed",
    )
    fix_percent = fields.Float(string="Fixed percentage (%)")

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

    # def calculate_section(self, base):
    #     self.ensure_one()
    #     for section in self.section_ids:
    #         if section.amount_from <= base <= section.amount_to:
    #             return base * section.percent / 100.0
    #     return 0.0


class AccountTaxIncomeSection(models.Model):
    _name = "account.tax.income.section"
    _description = "Income taxes section"
    _rec_name = 'amount_to'

    tax_id = fields.Many2one("account.tax.income", string="Income Tax")
    amount_from = fields.Float(string="Amount From")
    amount_to = fields.Float(string="Amount To")
    tax_rate_percent = fields.Float(string="Tax Rate (%)")

    def name_get(self):
        res = []
        for rec in self:
            # res.append((rec.id, rec.number + " - " + rec.name))
            name = '%s%%' % rec.tax_rate_percent
            res.append((rec.id, name))
        return res


