# -*- coding: utf-8 -*-
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_buy(self, procurements):
        # The flag lets purchase.order.line.create()/write() know that the
        # lines come from the "Buy" procurement (MTO / replenishment) flow.
        return super(StockRule, self.with_context(
            mto_expand_subproducts=True))._run_buy(procurements)
