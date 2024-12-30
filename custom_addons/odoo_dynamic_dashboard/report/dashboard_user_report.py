# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from psycopg2.extensions import AsIs
from odoo import api, fields, models, tools


class UserReport(models.Model):
    _name = "dashboard.user.report"
    _description = "User Analysis Report"
    _auto = False
    _order = 'updated_date asc'

    user_id = fields.Many2one('res.users', 'User', readonly=True)
    login = fields.Char('Login', readonly=True)
    display_name = fields.Char('User Name', readonly=True)
    updated_date = fields.Datetime('Date', readonly=True)
    alias_total_discusses = fields.Integer('Discuss', readonly=True)
    alias_total_calendars = fields.Integer('Calendar', readonly=True)
    alias_total_tickets = fields.Integer('Helpdesk', readonly=True)
    alias_total_partners = fields.Integer('Contacts', readonly=True)
    alias_total_attendances = fields.Integer('Attendances', readonly=True)
    alias_total_crms = fields.Integer('CRM', readonly=True)
    alias_total_sales = fields.Integer('Sales', readonly=True)
    alias_total_products = fields.Integer('Products', readonly=True)
    alias_total_accountings = fields.Integer('Accounting', readonly=True)
    alias_total_emails = fields.Integer('Email Marketing', readonly=True)
    alias_total_purchases = fields.Integer('Purchase', readonly=True)
    alias_total_inventory = fields.Integer('Inventory', readonly=True)
    alias_total_employees = fields.Integer('Employees', readonly=True)
    alias_total_time_offs = fields.Integer('Time Off', readonly=True)
    alias_total_freight = fields.Integer('Freight', readonly=True)
    alias_total_trading = fields.Integer('Freight Trading', readonly=True)
    alias_total_langson = fields.Integer('Lang Son', readonly=True)

