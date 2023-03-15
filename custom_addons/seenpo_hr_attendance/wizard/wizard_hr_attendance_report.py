# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime

from odoo import fields, models
from dateutil.relativedelta import relativedelta


class SeenpoHrAttendanceReportWizard(models.TransientModel):
    _name = "seenpo.hr.attendance.report.wizard"
    _description = "Wizard for reporting attendance timesheet"

    def _get_default_report_type(self):
        return self._context.get("report_type")

    date_month_report = fields.Date("Report month", default=fields.Date.today())
    date_year_report = fields.Selection([
        (str(num), str(num)) for num in range(2010, datetime.datetime.now().year + 1)
    ], 'Report year', default=str(datetime.datetime.now().year))
    report_type = fields.Char(string="Report Type", readonly=True, store=False,
                              default=_get_default_report_type)

    def action_download_report(self):
        self.ensure_one()

        report_type = self._context.get("report_type")
        if report_type == "annual_leave":
            return self.download_annual_leave_report()
        else:
            return self.download_timesheet_report()

    def download_annual_leave_report(self):
        self.ensure_one()

        today = datetime.datetime.now()
        report_year = int(self.date_year_report)
        to_month = 12
        if report_year == today.year:
            to_month = today.month
        elif report_year > today.year:
            to_month = 1

        report_date = datetime.date(report_year, to_month, 31 if to_month == 12 else today.day)

        employees = self.env['hr.employee'].search(
            [
                '&',
                ("bio_user_id", "!=", False),
                '|',
                ('active', '=', True),
                ('active', '=', False)
            ]
        )
        emp_ids = employees.ids
        allocations = self.env['hr.leave.allocation'].sudo().search(
            [
                ("state", "=", "validate"),
                ("employee_id", "in", emp_ids),
                ("date_from", "<=", report_date),
                ("date_to", ">=", report_date)
            ]
        )

        first_date_of_report_year = datetime.datetime(report_date.year, 1, 1)
        if report_date.year < today.year:
            last_date_of_report_year = datetime.datetime(report_date.year, 12, 31)
        else:
            last_date_of_report_year = today
        leaves = self.env['hr.leave'].sudo().search(
            [
                '&', '&',
                ("state", "=", "validate"),
                ("employee_id", "in", emp_ids),
                '|',
                '&',
                ("date_from", ">=", first_date_of_report_year),
                ("date_from", "<=", last_date_of_report_year),
                '&',
                ("date_to", ">=", first_date_of_report_year),
                ("date_to", "<=", last_date_of_report_year)
            ]
        )

        arr_employees_eval = []
        order_num = 0
        for idx, emp in enumerate(employees):
            if emp.departure_date and emp.departure_date.strftime('%Y%m') < today.strftime('%Y%m'):
                continue

            order_num += 1

            total_working_time = ''
            if emp.contract_date_start:
                diff = relativedelta(today, emp.contract_date_start)
                total_working_time = f"{diff.years} năm {diff.months} tháng {diff.days} ngày"

            allocation = [r for r in allocations if r.employee_id.id == emp.id]
            annual_leaves = allocation[0].number_of_days if allocation else 0

            arr_total_leaves = {}
            count_total_leaves = 0
            for i in range(to_month):
                current_month = i + 1
                emp_lefts = [l for l in leaves if l.employee_id.id == emp.id and
                             (l.date_from.year == report_date.year and l.date_from.month == current_month
                             or l.date_to.year == report_date.year and l.date_to.month == current_month)]
                count_total_leaves_of_month = 0
                for emp_left in emp_lefts:
                    if emp_left.date_from.month == emp_left.date_to.month:
                        count_total_leaves_of_month += emp_left.number_of_days
                    else:
                        ''' Calculate in case of leave dates are continue of two months.
                        If it is more than continue of two months (e.g. 3 months, 4 months...) then it should be
                        solved by manually splitting the leave days back to two months continuously.
                        '''
                        last_day_of_month = (emp_left.date_from + relativedelta(day=31)).day
                        leave_days_of_month_from = last_day_of_month - emp_left.date_from.day + 1
                        if current_month == emp_left.date_from.month:
                            count_total_leaves_of_month += leave_days_of_month_from
                        elif current_month == emp_left.date_to.month:
                            leave_days_of_month_to = emp_left.number_of_days - leave_days_of_month_from
                            count_total_leaves_of_month += leave_days_of_month_to

                arr_total_leaves[current_month] = count_total_leaves_of_month
                count_total_leaves += count_total_leaves_of_month

            obj_emp = {
                "order": order_num,
                "emp_code": f"NV{order_num:02d}",
                "emp_name": emp.name,
                "department": emp.department_id.name[:3] if emp.department_id else False,
                "date_start": emp.contract_date_start.strftime('%d/%m/%Y') if emp.contract_date_start else False,
                "total_working_time": total_working_time,
                "annual_leaves": annual_leaves,
                "arr_total_leaves": arr_total_leaves,
                "total_leaves": count_total_leaves,
                "total_leaves_remaining": annual_leaves - count_total_leaves
            }

            arr_employees_eval.append(obj_emp)

        data = {
            'current_date': today.strftime('%d/%m/%Y'),
            'report_year': report_date.strftime('%Y'),
            'to_month': to_month,
            'records': arr_employees_eval
        }

        return self.env.ref('seenpo_hr_attendance.seenpo_hr_attendance_annual_leave_report').report_action(self, data=data)

    def download_timesheet_report(self):
        self.ensure_one()

        today = datetime.datetime.now()
        month_year = self.date_month_report.strftime("%m/%Y")
        first_date_of_month = datetime.date(self.date_month_report.year, self.date_month_report.month, 1)
        last_date_of_month = self.date_month_report + relativedelta(day=31)
        '''Create an array of dates and day of week in header'''
        arr_dates_in_header = {}
        current_date = first_date_of_month
        while current_date <= last_date_of_month:
            day_of_week = current_date.weekday()
            if day_of_week == 0:
                day_of_week_text = 'T2'
            elif day_of_week == 1:
                day_of_week_text = 'T3'
            elif day_of_week == 2:
                day_of_week_text = 'T4'
            elif day_of_week == 3:
                day_of_week_text = 'T5'
            elif day_of_week == 4:
                day_of_week_text = 'T6'
            elif day_of_week == 5:
                day_of_week_text = 'T7'
            else:
                day_of_week_text = 'CN'

            arr_dates_in_header[current_date.strftime('%Y-%m-%d')] = day_of_week_text
            current_date = current_date + relativedelta(days=1)

        logs = self.env['seenpo.hr.attendance.bio.log'].search(
            [
                ("check_in_date", ">=", first_date_of_month),
                ("check_in_date", "<=", last_date_of_month)
            ]
        )
        employees = self.env['hr.employee'].search(
            [
                '&',
                ("bio_user_id", "!=", False),
                '|',
                ('active', '=', True),
                ('active', '=', False)
            ]
        )
        leaves = self.env['hr.leave'].sudo().search(
            [
                '&',
                ("state", "=", "validate"),
                '|',
                '&',
                ("date_from", ">=", first_date_of_month),
                ("date_from", "<=", last_date_of_month),
                '&',
                ("date_to", ">=", first_date_of_month),
                ("date_to", "<=", last_date_of_month)
            ]
        )
        public_holidays = self.env['resource.calendar.leaves'].sudo().search(
            [
                '&', '&', '&',
                ("time_type", "=", "leave"),
                ("resource_id", "=", False),
                ("holiday_id", "=", False),
                '|',
                '&',
                ("date_from", ">=", first_date_of_month),
                ("date_from", "<=", last_date_of_month),
                '&',
                ("date_to", ">=", first_date_of_month),
                ("date_to", "<=", last_date_of_month)
            ]
        )
        '''Create an array of employees with leaves'''
        arr_employees_eval = []
        last_row_total = {}
        count_working_days_total = 0
        count_unpaid_total = 0
        count_paid_total = 0
        count_public_holiday_total = 0
        order_num = 0
        for idx, emp in enumerate(employees):
            if emp.departure_date and emp.departure_date.strftime('%Y%m') < today.strftime('%Y%m'):
                continue

            order_num += 1

            arr_leaves = {}
            count_working_days = 0
            count_unpaid = 0
            count_paid = 0
            count_public_holiday = 0

            obj_emp = {
                "order": order_num,
                "emp_code": f"NV{order_num:02d}",
                "name": emp.name,
                "department": emp.department_id.name[:3] if emp.department_id else False,
                "arr_leaves": arr_leaves,
                "count_working_days": count_working_days,
                "count_unpaid": count_unpaid,
                "count_public_holiday": count_public_holiday,
                "count_paid": count_paid
            }

            emp_logs = [log for log in logs if log.bio_user_id == emp.bio_user_id]
            for d_key, d_value in arr_dates_in_header.items():
                arr_leaves[d_key] = ''

                if not (d_key in last_row_total):
                    last_row_total[d_key] = 0

                '''Skip Sunday, departure and future dates printing'''
                if d_key > today.strftime('%Y-%m-%d'):
                    continue
                if d_value == 'CN':
                    arr_leaves[d_key] = 'SUN'
                    continue
                if emp.departure_date and emp.departure_date.strftime('%Y-%m-%d') < d_key:
                    arr_leaves[d_key] = 'OUT'
                    continue

                holidays = [h for h in public_holidays if h.date_from.date().strftime('%Y-%m-%d') <= d_key
                            <= h.date_to.date().strftime('%Y-%m-%d')]
                if holidays:
                    if d_value == 'T7':
                        count_public_holiday += 0.5
                        arr_leaves[d_key] = 'L/2'
                    else:
                        count_public_holiday += 1
                        arr_leaves[d_key] = 'L'
                    continue

                emp_lefts = [l for l in leaves if l.date_from.date().strftime('%Y-%m-%d') <= d_key
                            <= l.date_to.date().strftime('%Y-%m-%d') and l.employee_id.id == emp.id]
                if emp_lefts:
                    emp_left = emp_lefts[0]
                    arr_leaves[d_key] = 'P'
                    if emp_left.holiday_status_id:
                        if 'Sick' in emp_left.holiday_status_id.name:
                            arr_leaves[d_key] = 'O'
                        elif 'Unpaid' in emp_left.holiday_status_id.name:
                            arr_leaves[d_key] = 'K'

                    if emp_left.number_of_days == 0.5:
                        arr_leaves[d_key] += '/2'

                    if emp_left.holiday_status_id and 'Unpaid' in emp_left.holiday_status_id.name:
                        count_unpaid += 0.5 if emp_left.number_of_days == 0.5 else 1
                    else:
                        count_paid += 0.5 if emp_left.number_of_days == 0.5 else 1

                    continue

                emp_checked_in = [log for log in emp_logs if log.check_in_date.date().strftime('%Y-%m-%d') == d_key]
                if d_value == 'T7':
                    count_working_days += 0.5
                    if emp_checked_in:
                        arr_leaves[d_key] = 'x/2'
                    else:
                        arr_leaves[d_key] = 'y/2'
                else:
                    count_working_days += 1
                    if emp_checked_in:
                        arr_leaves[d_key] = 'x'
                    else:
                        arr_leaves[d_key] = 'y'

                '''Calculate total of last row'''
                if arr_leaves[d_key] == 'x' or arr_leaves[d_key] == 'y':
                    last_row_total[d_key] += 1
                elif arr_leaves[d_key] == 'x/2' or arr_leaves[d_key] == 'y/2':
                    last_row_total[d_key] += 0.5

            count_working_days_total += count_working_days
            count_unpaid_total += count_unpaid
            count_public_holiday_total += count_public_holiday
            count_paid_total += count_paid

            '''Send these values to report views'''
            obj_emp["arr_leaves"] = arr_leaves
            obj_emp["count_working_days"] = count_working_days
            obj_emp["count_unpaid"] = count_unpaid
            obj_emp["count_public_holiday"] = count_public_holiday
            obj_emp["count_paid"] = count_paid
            arr_employees_eval.append(obj_emp)

        data = {
            'signed_date_text': f"TP.Hồ Chí Minh, ngày {today.day} tháng {today.month} năm {today.year}",
            'month_year': month_year,
            'first_date_of_month': first_date_of_month,
            'last_day_of_month': last_date_of_month,
            'arr_dates_in_header': arr_dates_in_header,
            'records': arr_employees_eval,
            'last_row_total': last_row_total,
            'count_working_days_total': count_working_days_total,
            'count_unpaid_total': count_unpaid_total,
            'count_public_holiday_total': count_public_holiday_total,
            'count_paid_total': count_paid_total,
        }

        return self.env.ref('seenpo_hr_attendance.seenpo_hr_attendance_timesheet_report').report_action(self, data=data)
