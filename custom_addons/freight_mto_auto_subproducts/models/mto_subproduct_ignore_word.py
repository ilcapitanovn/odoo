# -*- coding: utf-8 -*-
from odoo import fields, models


class MtoSubproductIgnoreWord(models.Model):
    _name = 'mto.subproduct.ignore.word'
    _description = 'MTO Suggestion Ignore Word'
    _order = 'name'

    name = fields.Char(
        string='Word or phrase', required=True,
        help="Ignored when suggesting sub-products by name / vendor similarity. "
             "Every word of an entry is ignored; an entry made of several "
             "words (e.g. 'Entrusted Export Service') also hides products whose "
             "name contains that whole phrase (other main products).")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This word or phrase is already in the list.'),
    ]
