# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime

from dateutil.relativedelta import *
from odoo import models, fields, api
from odoo.osv import expression
from ast import literal_eval


class DashboardBlock(models.Model):
    _name = "dashboard.block"
    _description = "Dashboard Blocks"
    _rec_name = "name"

    def get_default_action(self):
        action_id = self.env.ref('odoo_dynamic_dashboard.action_dynamic_dashboard')
        if action_id:
            return action_id.id
        else:
            return False

    name = fields.Char(string="Name", help='Name of the block')
    field_id = fields.Many2one('ir.model.fields', 'Measured Field',domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['float','integer','monetary'])]")
    fa_icon = fields.Char(string="Icon")
    graph_size = fields.Selection(
        selection=[("col-lg-4", "Small"), ("col-lg-6", "Medium"), ("col-lg-12", "Large")],
        string="Graph Size",default='col-lg-4')
    operation = fields.Selection(
        selection=[("sum", "Sum"), ("avg", "Average"), ("count", "Count"), ("custom", "Custom")],
        string="Operation", help='Tile Operation that needs to bring values for tile')

    graph_type = fields.Selection(
        selection=[("bar", "Bar"), ("radar", "Radar"), ("pie", "Pie"), ("line", "Line"), ("doughnut", "Doughnut")],
        string="Chart Type", help='Type of Chart')
    measured_field = fields.Many2one("ir.model.fields", "Measured Field")
    x_measured_custom = fields.Char(string="Select Custom", help='Write custom fields in SELECT query here')
    x_join_custom = fields.Char(string="Join Custom", help='Write FROM and JOIN custom in query here')
    client_action = fields.Many2one('ir.actions.client', default = get_default_action)

    type = fields.Selection(
        selection=[("graph", "Chart"), ("tile", "Tile"), ("table", "Table")],
        string="Type", help='Type of Block ie, Chart or Tile or Table')
    x_axis = fields.Char(string="X-Axis")
    y_axis = fields.Char(string="Y-Axis")
    group_by = fields.Many2one("ir.model.fields", store=True, string="Group by(Y-Axis)", help='Field value for Y-Axis')
    x_group_by = fields.Char(string="Group by Custom", help='Write group by custom fields in query here')
    tile_color = fields.Char(string="Tile Color", help='Primary Color of Tile')
    text_color = fields.Char(string="Text Color", help='Text Color of Tile')
    fa_color = fields.Char(string="Icon Color", help='Icon Color of Tile')
    filter = fields.Char(string="Filter")
    x_date_range = fields.Selection(
        selection=[("all", "All data"), ("today", "Today"), ("yesterday", "Yesterday"), ("this_week", "This week"),
                   ("last_week", "Last week"), ("next_week", "Next week"), ("this_month", "This month"), ("last_month", "Last month"),
                   ("next_month", "Next month"), ("this_quarter", "This quarter"), ("last_quarter", "Last quarter"),
                   ("next_quarter", "Next quarter"), ("this_year", "This year"), ("last_year", "Last year"), ("next_year", "Next year")],
        string="Date range", help='Period time filter for report')
    x_compared_to = fields.Selection(
        selection=[("previous_week", "Previous week"), ("previous_month", "Previous month"), ("year_before", "Year before")],
        string="Compared To", help='See how it compared to previous')
    model_id = fields.Many2one('ir.model', 'Model')
    model_name = fields.Char(related='model_id.model', readonly=True)

    filter_by = fields.Many2one("ir.model.fields", string=" Filter By")
    filter_values = fields.Char(string="Filter Values")

    sequence = fields.Integer(string="Sequence")
    edit_mode = fields.Boolean(default=False, invisible=True)

    def get_comparison_field(self, param_rec):
        result = ""
        if param_rec.model_name == "crm.lead":
            result = "date_deadline"
        elif param_rec.model_name == "res.partner":
            result = "create_date"
        elif param_rec.model_name == "mail.activity":
            result = "date_deadline"
        elif param_rec.model_name == "sale.order":
            result = "date_order"

        return result

    def get_date_range_filter(self, param_rec, filter_field):
        dic_date_range = {
            "from_date": "",
            "to_date": "",
            "filter_conditions": []
        }

        today = fields.Date.context_today(self)

        from_date = to_date = ""
        new_conditions = []
        if param_rec.x_date_range == "today":
            from_date = to_date = today.strftime('%Y-%m-%d 00:00:00')
            new_conditions = [(filter_field, '=', from_date)]

        elif param_rec.x_date_range == "yesterday":
            from_date = to_date = (today - relativedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = [(filter_field, '=', from_date)]

        elif param_rec.x_date_range == "this_week":
            from_date = (today + relativedelta(weeks=-1, days=1, weekday=0)).strftime('%Y-%m-%d 00:00:00')
            to_date = (today + relativedelta(weekday=6)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<=', to_date)]

        elif param_rec.x_date_range == "last_week":
            from_date = (today + relativedelta(weeks=-2, days=1, weekday=0)).strftime('%Y-%m-%d 00:00:00')
            to_date = (today + relativedelta(weeks=-1, weekday=6)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<=', to_date)]

        elif param_rec.x_date_range == "next_week":
            from_date = (today + relativedelta(weeks=0, days=1, weekday=0)).strftime('%Y-%m-%d 00:00:00')
            to_date = (today + relativedelta(weeks=1, weekday=6)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<=', to_date)]

        elif param_rec.x_date_range == "this_month":
            from_date = (today + relativedelta(day=1)).strftime('%Y-%m-%d 00:00:00')
            to_date = (today + relativedelta(day=31)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<=', to_date)]

        elif param_rec.x_date_range == "last_month":
            from_date = (today - relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')
            to_date = today.strftime('%Y-%m-01 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "next_month":
            from_date = (today + relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')
            to_date = (today + relativedelta(months=2)).strftime('%Y-%m-01 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "this_quarter":
            current_quarter = int((today.month - 1) / 3 + 1)
            from_date = datetime.datetime(today.year, 3 * current_quarter - 2, 1).strftime('%Y-%m-%d 00:00:00')
            to_date = (from_date + relativedelta(months=3)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "last_quarter":
            previous_3_months = today - relativedelta(months=3)
            last_quarter = int((previous_3_months.month - 1) / 3 + 1)
            from_date = datetime.datetime(previous_3_months.year, 3 * last_quarter - 2, 1)
            to_date = (from_date + relativedelta(months=3)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date.strftime('%Y-%m-%d 00:00:00')), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "next_quarter":
            next_3_months = today + relativedelta(months=3)
            next_quarter = int((next_3_months.month - 1) / 3 + 1)
            from_date = datetime.datetime(next_3_months.year, 3 * next_quarter - 2, 1)
            to_date = (from_date + relativedelta(months=3)).strftime('%Y-%m-%d 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date.strftime('%Y-%m-%d 00:00:00')), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "this_year":
            from_date = today.strftime('%Y-01-01 00:00:00')
            to_date = (today + relativedelta(years=1)).strftime('%Y-01-01 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "last_year":
            from_date = (today - relativedelta(years=1)).strftime('%Y-01-01 00:00:00')
            to_date = today.strftime('%Y-01-01 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<', to_date)]

        elif param_rec.x_date_range == "next_year":
            from_date = (today + relativedelta(years=1)).strftime('%Y-01-01 00:00:00')
            to_date = (today + relativedelta(years=2)).strftime('%Y-01-01 00:00:00')
            new_conditions = ['&', (filter_field, '>=', from_date), (filter_field, '<', to_date)]

        if new_conditions:
            dic_date_range = {
                "from_date": from_date,
                "to_date": to_date,
                "filter_conditions": new_conditions
            }

        return dic_date_range

    def append_date_range_filter(self, domain, param_rec):
        updated_domain = domain
        if param_rec.x_date_range and param_rec.x_date_range != "all":
            filter_field = self.get_comparison_field(param_rec)
            if not filter_field:
                return updated_domain
            # else:
            #     filter_field = ('cast(%s as Date)' % filter_field)

            # if not param_rec.x_date_range or param_rec.x_date_range == "all":
            #     return domain

            #sprint = '%s of from_date = %s and to_date = %s' % param_rec.x_date_range, from_date, to_date
            #print(sprint)

            dic_date_range = self.get_date_range_filter(param_rec, filter_field)
            new_conditions = dic_date_range["filter_conditions"]

            if new_conditions:
                updated_domain = expression.AND([
                    expression.normalize_domain(domain),
                    expression.normalize_domain(new_conditions)
                ])

        return updated_domain

    def get_domain_compared_to(self, domain, param_rec):
        previous_domain = []

        today = fields.Date.context_today(self)

        filter_field = self.get_comparison_field(param_rec)
        if not filter_field:
            return previous_domain
        # else:
        #     filter_field = ('cast(%s as Date)' % filter_field)

        previous_conditions = []
        if not param_rec.x_compared_to:
            return previous_domain

        dic_date_range = self.get_date_range_filter(param_rec, filter_field)
        from_date = to_date = today
        if dic_date_range["from_date"] and dic_date_range["to_date"]:
            try:
                from_date = datetime.datetime.strptime(dic_date_range["from_date"], "%Y-%m-%d %H:%M:%S")
                to_date = datetime.datetime.strptime(dic_date_range["to_date"], "%Y-%m-%d %H:%M:%S")
            except:
                from_date = to_date = today

        if param_rec.x_compared_to == "previous_week":
            previous_from_date = (from_date + relativedelta(weeks=-2, days=1, weekday=0)).strftime('%Y-%m-%d 00:00:00')
            previous_to_date = (from_date + relativedelta(weeks=-1, weekday=6)).strftime('%Y-%m-%d 00:00:00')
            previous_conditions = ['&', (filter_field, '>=', previous_from_date), (filter_field, '<=', previous_to_date)]

        elif param_rec.x_compared_to == "previous_month":
            previous_from_date = (from_date - relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')
            previous_to_date = from_date.strftime('%Y-%m-01 00:00:00')
            previous_conditions = ['&', (filter_field, '>=', previous_from_date), (filter_field, '<', previous_to_date)]

        elif param_rec.x_compared_to == "year_before":
            previous_from_date = (from_date - relativedelta(years=1)).strftime('%Y-%m-01 00:00:00')
            previous_to_date = (from_date - relativedelta(years=1) + relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')
            previous_conditions = ['&', (filter_field, '>=', previous_from_date), (filter_field, '<', previous_to_date)]

        if previous_conditions:
            previous_domain = expression.AND([
                expression.normalize_domain(domain),
                expression.normalize_domain(previous_conditions)
            ])

        return previous_domain

    def get_dashboard_vals(self, action_id):
        """Dashboard block values"""
        block_id = []
        dashboard_block = self.env['dashboard.block'].sudo().search([('client_action', '=', int(action_id))])
        for rec in dashboard_block:
            color = rec.tile_color if rec.tile_color else '#1f6abb;'
            icon_color = rec.tile_color if rec.tile_color else '#1f6abb;'
            text_color = rec.text_color if rec.text_color else '#FFFFFF;'
            date_range_label = dict(self._fields['x_date_range'].selection).get(rec.x_date_range)
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec.fa_icon,
                'cols': rec.graph_size,
                'color': 'background-color: %s;' % color,
                'text_color': 'color: %s;' % text_color,
                'icon_color': 'color: %s;' % icon_color,
                'date_range': date_range_label or 'All'
            }
            domain = []
            if rec.filter:
                domain = expression.AND([literal_eval(rec.filter)])

            # Save domain before date range filter to make previous domain if compared to selected
            domain_compared_to = []
            if rec.x_compared_to:
                domain_compared_to = domain

            # Add date range filter to domain filter if selected
            domain = self.append_date_range_filter(domain, rec)

            current_total = previous_total = 0
            try:
                if rec.model_name:
                    if rec.type == 'graph':
                        if rec.operation == "custom":
                            query = self.env[rec.model_name].get_query_custom(domain, rec.operation,
                                                                              rec.x_measured_custom,
                                                                              rec.x_join_custom,
                                                                              group_by_custom=rec.x_group_by)
                        else:
                            query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field,
                                                                       group_by=rec.group_by)
                        self._cr.execute(query)
                        records = self._cr.dictfetchall()
                        print(query,"query")
                        print(records,"records")
                        x_axis = []
                        for record in records:
                            x_axis.append(record.get(rec.group_by.name))
                        y_axis = []
                        for record in records:
                            y_axis.append(record.get('value'))
                        vals.update({'x_axis': x_axis, 'y_axis': y_axis})

                    elif rec.type == 'table':
                        if rec.operation == "custom":
                            query = self.env[rec.model_name].get_query_custom(domain, rec.operation,
                                                                              rec.x_measured_custom,
                                                                              rec.x_join_custom,
                                                                              group_by_custom=rec.x_group_by)
                        else:
                            query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field,
                                                                       group_by=rec.group_by)
                        self._cr.execute(query)
                        records = self._cr.dictfetchall()
                        print(query, "query")
                        print(records, "records")
                        row_headers = []
                        for i in range(len(self._cr.description)):
                            row_headers.append(self._cr.description[i].name)
                        row_values = []
                        row_totals = [0] * len(row_headers)
                        row_totals[0] = "Report Total"
                        for record in records:
                            row_values.append(record)
                            for i in range(len(record)):
                                if i > 0:
                                    val = record.get(row_headers[i])
                                    if val:
                                        if type(val) == int or type(val) == float:
                                            n = row_totals[i] or 0
                                            row_totals[i] = n + val
                                        else:
                                            val_num = self.currency_to_float(val)
                                            if val_num > 0:
                                                n = self.currency_to_float(row_totals[i])
                                                total = n + val_num
                                                row_totals[i] = '$' + '{:3,.2f}'.format(total)  # Convert back to currency

                        vals.update({'row_headers': row_headers, 'row_values': row_values, 'row_totals': row_totals})

                    else:
                        if rec.operation == "custom":
                            query = self.env[rec.model_name].get_query(domain, rec.operation, rec.x_measured_custom)
                        else:
                            query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field)
                        self._cr.execute(query)
                        records = self._cr.dictfetchall()
                        magnitude = 0
                        current_total = total = records[0].get('value')
                        while abs(total) >= 1000:
                            magnitude += 1
                            total /= 1000.0
                        # add more suffixes if you need them
                        if rec.operation == "count":
                            val = '%.f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
                        else:
                            val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

                        # if rec.measured_field.ttype == 'monetary':
                            # amount = str(
                            #     value) + currency_id.symbol if currency_id.position == 'after' else currency_id.symbol + str(
                            #     value)
                        records[0]['value'] = val

                        # Calculate previous value
                        if rec.x_compared_to:
                            domain_compared_to = self.get_domain_compared_to(domain_compared_to, rec)
                            if domain_compared_to:
                                if rec.operation == "custom":
                                    query_compared_to = self.env[rec.model_name].get_query(domain_compared_to, rec.operation, rec.x_measured_custom)
                                else:
                                    query_compared_to = self.env[rec.model_name].get_query(domain_compared_to, rec.operation, rec.measured_field)
                                self._cr.execute(query_compared_to)
                                records_compared_to = self._cr.dictfetchall()
                                previous_total = records_compared_to[0].get('value')
                                if previous_total != 0:
                                    change_rate = current_total * 100 / previous_total - 100
                                    if change_rate >= 0:
                                        change_rate_val = '<i class="fa fa-arrow-up" style="color: #05E672"></i> ' + ('%.2f' % change_rate) + '%'
                                    else:
                                        change_rate_val = '<i class="fa fa-arrow-down" style="color: #DF3056"></i> ' + ('%.2f' % change_rate) + '%'
                                else:
                                    change_rate_val = ''
                                records[0]['change_rate'] = change_rate_val

                        vals.update(records[0])

            except:
                print("An exception occurred")

            block_id.append(vals)
        print(block_id,"dhressssssssssss")
        return block_id

    def currency_to_float(self, currency):
        result = 0

        if currency and currency.startswith('$'):
            val_num = currency[1:]  # remove first character
            try:
                result = float(val_num.replace(',', ''))
            except ValueError:
                print(currency + ' is not a numeric')

        return result

class DashboardBlockLine(models.Model):
    _name = "dashboard.block.line"

    sequence = fields.Integer(string="Sequence")
    block_size = fields.Integer(string="Block size")
