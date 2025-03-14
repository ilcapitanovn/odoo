# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import codecs
import csv
import datetime
import time

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
import requests
import os.path


class SeenpoHrAttendanceBioLog(models.Model):
    _name = "seenpo.hr.attendance.bio.log"
    _description = "Seenpo HR Attendance Bio Log"
    _order = "bio_user_id, check_in_date"
    _rec_name = "id"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin"]
    _session = requests.Session()
    _bio_config = {
        "url": "http://vtoan.ddns.net:8081",
        "username": "admin",
        "password": "admin"
    }
    _no_reason = 'ko lý do'

    ''' This user_id should be reference key ID added in the employee table '''
    bio_user_id = fields.Char(string='User ID', readonly=True, index=True)
    card_number = fields.Char(string='Card No.', readonly=True)
    employee = fields.Char(string='Employee', readonly=True)
    check_in_date = fields.Datetime(string='Date', readonly=True)
    first_in_time = fields.Char(string='First In Time', readonly=True)
    last_out_time = fields.Char(string='Last Out Time', readonly=True)
    reason = fields.Char(string='Reason', tracking=True, translate=True)

    hr_employee_id = fields.Many2one(
        comodel_name="hr.employee", string="HR Employee Reference", readonly=True, tracking=True
    )
    hr_employee_name_related = fields.Char(related="hr_employee_id.name", readonly=True, store=False)
    hr_employee_bio_user_id = fields.Char(related="hr_employee_id.bio_user_id", readonly=True, store=False)
    hr_employee_active = fields.Boolean(related="hr_employee_id.active", string="Employee Active", readonly=True, store=False)
    hr_employee_name = fields.Char(compute="_compute_hr_employee", string="Employee", readonly=True, store=True)
    active = fields.Boolean(compute="_compute_hr_employee", string='Active', readonly=True, store=True)
    check_in_date_display = fields.Date(compute="_compute_check_in_date_display", string='Date', readonly=True, store=False)
    is_check_in_late = fields.Boolean(compute="_compute_is_check_in_late", string="Late", readonly=True, store=False)
    reason_display = fields.Char(compute="_compute_reason_display", string="Reason", readonly=True, store=False)
    is_permission_group_user = fields.Boolean(compute="_compute_is_permission_group_user", string="Check Permission")

    @api.model
    def _update_hr_employee_id_by_upgrading(self):
        employees = self.env["hr.employee"].sudo().search(
            [
                '&',
                ("bio_user_id", "!=", False),
                '|',
                ('active', '=', True),
                ('active', '=', False)
            ]
        )
        logs = self.search([('hr_employee_id', '=', False)])
        for log in logs:
            for emp in employees:
                if emp["bio_user_id"] == log.bio_user_id:
                    log.write({'hr_employee_id': emp.id})

    @api.model
    def fields_get(self, all_fields=None, attributes=None):
        fields_to_hide = ['employee', 'hr_employee_name_related', 'hr_employee_bio_user_id', 'hr_employee_active']
        res = super(SeenpoHrAttendanceBioLog, self).fields_get(all_fields, attributes=attributes)
        for field in fields_to_hide:
            if field in res:
                res[field]['searchable'] = False
        return res

    @api.depends('is_permission_group_user')
    def _compute_is_permission_group_user(self):
        res_user = self.env['res.users'].sudo().search([('id', '=', self._uid)])
        if res_user.has_group('seenpo_hr_attendance.group_seenpo_hr_attendance_user') \
                and not res_user.has_group('seenpo_hr_attendance.group_seenpo_hr_attendance_manager'):
            self.is_permission_group_user = True
        else:
            self.is_permission_group_user = False

    @api.depends('check_in_date')
    def _compute_check_in_date_display(self):
        for rec in self:
            rec.check_in_date_display = rec.check_in_date.date()

    @api.depends('first_in_time')
    def _compute_is_check_in_late(self):
        accepted_check_in_time_late = '08:15:00'
        for rec in self:
            rec.is_check_in_late = rec.first_in_time and rec.first_in_time > accepted_check_in_time_late

    @api.depends('is_check_in_late', 'reason')
    def _compute_reason_display(self):
        for rec in self:
            rec.reason_display = rec.reason
            if rec.is_check_in_late and not rec.reason:
                rec.reason_display = self._no_reason

    @api.depends('hr_employee_name_related', 'hr_employee_bio_user_id', 'hr_employee_active')
    def _compute_hr_employee(self):
        """ This code has performance issue """
        # match_employees = self.env["hr.employee"].search(
        #     [
        #         '&',
        #         ("bio_user_id", "!=", False),
        #         '|',
        #         ('active', '=', True),
        #         ('active', '=', False)
        #     ]
        # )
        # for rec in self:
        #     rec.hr_employee_name = ''
        #     rec.active = True
        #     if match_employees:
        #         for emp in match_employees:
        #             if emp["bio_user_id"] == rec.bio_user_id:
        #                 rec.hr_employee_name = emp["name"]
        #                 rec.active = emp["active"]

        for rec in self:
            rec.hr_employee_name = rec.hr_employee_name_related
            rec.active = rec.hr_employee_active

    '''
    This method will be used by the scheduled actions to sync missing previous attendances of a user.
    '''
    def manual_refresh_bio_attendance_log_by_month(self, date_specified=fields.Date.today()):
        try:
            print(f"Manual refresh bio attendance for month of date: {date_specified}")
            today = date_specified
            last_month_start = today + relativedelta(months=-1, day=1)
            last_month_end = last_month_start + relativedelta(months=1, days=-1)
            current_month_start = today.replace(day=1)
            print(f"last_month_start = {last_month_start}")
            print(f"last_month_end = {last_month_end}")
            print(f"current_month_start = {current_month_start}")
            print(f"current_month_end = {today}")
            from_date = last_month_start
            to_date = date_specified
            add_day = datetime.timedelta(days=1)
            while from_date <= to_date:
                print(f"It's calling the [refresh_bio_attendance_log] of date: {from_date}")
                result = self.refresh_bio_attendance_log(from_date)
                if result:
                    print('---SUCCESS---')
                else:
                    print('---FAILED---')
                from_date += add_day

            # from_date = (today + datetime.timedelta(days=1))  # .strftime('%Y-%m-%d')
            # to_date = (today + datetime.timedelta(days=31))  # .strftime('%Y-%m-%d')
            # addDay = datetime.timedelta(days=1)
            # while from_date <= to_date:
            #     log(from_date, level='info')
            #     # model.refresh_bio_attendance_log(datetime.datetime.strptime("2024-03-30", "%Y-%m-%d"))
            #     # action = model.refresh_bio_attendance_log(from_date)
            #     action = True
            #     if action:
            #         log('SUCCESS', level='info')
            #     else:
            #         log('FAILED', level='info')
            #     from_date += addDay
        except requests.Timeout as e:
            print("Exception Timeout - manual_refresh_bio_attendance_log_by_month: " + str(e))
            return "There is timeout issue in bio log refreshing."
        except Exception as e:
            print("Exception general - manual_refresh_bio_attendance_log_by_month: " + str(e))
            return "There are errors in bio log refreshing."

    def refresh_bio_attendance_log(self, date_specified=fields.Date.today()):
        try:
            print(f"Refresh bio attendance for date: {date_specified}")
            # The Bio device only set download filename is always format of today
            # today = fields.Date.today()
            today = fields.Datetime.context_timestamp(self, fields.Datetime.now())  # now in local time zone
            filename = today.strftime('%m%d%y') + '.txt'

            self._load_bio_config_from_sys_params()
            self._get_bio_data(date_specified, date_specified)
            response = self._download_bio_data(filename)

            BioLog = self.env['seenpo.hr.attendance.bio.log']
            # dict_from_csv = {}
            if response.status_code == 200 and response.content:
                dict_content = csv.DictReader(response.text.splitlines())
            else:
                # raise_for_status will result in either nothing, a Client Error
                # for HTTP Response codes between 400 and 500 or a Server Error
                # for codes between 500 and 600
                response.raise_for_status()

            logs = BioLog.search(
                [
                    ("check_in_date", "=", date_specified)
                ]
            )

            employees = self.env["hr.employee"].sudo().search([("bio_user_id", "!=", False)])

            create_vals_list = []

            if logs:
                for row in dict_content:

                    user_id = row.get('User id')
                    card = row.get('Card No')
                    employee = row.get('Employee ID/ User Name')
                    check_in_date = date_specified
                    first_in_time = row.get('First In Time')
                    last_out_time = row.get('Last Out Time')

                    current_log = None
                    for log in logs:
                        if log['check_in_date'].date() == date_specified and log['bio_user_id'] == user_id:
                            current_log = log
                            break

                    if current_log:
                        if current_log['first_in_time'] != first_in_time or \
                                current_log['last_out_time'] != last_out_time:
                            current_log.update({
                                "first_in_time": first_in_time,
                                "last_out_time": last_out_time
                            })
                    else:
                        employee_id = False
                        hr_employees = employees.filtered(lambda emp: emp.bio_user_id == user_id)
                        if hr_employees:
                            employee_id = hr_employees[0].id

                        create_vals_list.append({
                            "bio_user_id": user_id,
                            "card_number": card,
                            "employee": employee,
                            "check_in_date": check_in_date,
                            "first_in_time": first_in_time,
                            "last_out_time": last_out_time,
                            "hr_employee_id": employee_id
                        })
            else:
                for row in dict_content:
                    user_id = row.get('User id')
                    card = row.get('Card No')
                    employee = row.get('Employee ID/ User Name')
                    check_in_date = date_specified
                    first_in_time = row.get('First In Time')
                    last_out_time = row.get('Last Out Time')

                    employee_id = False
                    hr_employees = employees.filtered(lambda emp: emp.bio_user_id == user_id)
                    if hr_employees:
                        employee_id = hr_employees[0].id

                    create_vals_list.append({
                        "bio_user_id": user_id,
                        "card_number": card,
                        "employee": employee,
                        "check_in_date": check_in_date,
                        "first_in_time": first_in_time,
                        "last_out_time": last_out_time,
                        "hr_employee_id": employee_id
                    })

            if create_vals_list:
                BioLog.create(create_vals_list)

            return True
        except requests.Timeout as e:
            print("Exception Timeout - refresh_bio_attendance_log: " + str(e))
            return "There is timeout issue in bio log refreshing."
        except Exception as e:
            print("Exception general - refresh_bio_attendance_log: " + str(e))
            return "There are errors in bio log refreshing."

    def _download_bio_data(self, filename):
        print(f"_download_bio_data - STARTED - {datetime.datetime.now()}")
        if not self._session:
            self._session = requests.Session()

        auth = (self._bio_config["username"], self._bio_config["password"])
        request_url = self._bio_config["url"] + "/" + filename
        return self._session.get(request_url, timeout=300, auth=auth)

    def _get_bio_data(self, from_date: fields.Date, to_date: fields.Date):
        print(f"_get_bio_data - STARTED - {datetime.datetime.now()}")
        if not self._session:
            self._session = requests.Session()

        auth = (self._bio_config["username"], self._bio_config["password"])
        from_year = from_date.strftime('%y')
        from_month = from_date.strftime('%m')
        from_day = from_date.strftime('%d')
        to_year = to_date.strftime('%y')
        to_month = to_date.strftime('%m')
        to_day = to_date.strftime('%d')
        params = f'?redirect=Dailylog.htm&failure=fail.htm&type=search_f_in_l_out_log&&sel=1&u_id=' \
                 f'&year={from_year}&mon={from_month}&day={from_day}' \
                 f'&year={to_year}&mon={to_month}&day={to_day}' \
                 f'&card=0&card=0&card=0&card=0&card=0&card=0&card=0&card=0' \
                 f'&fun_t=1&e_t=0&eid='

        request_url = self._bio_config["url"] + "/if.cgi" + params
        # response = self._session.get(request_url, timeout=10, auth=auth, verify=False)
        response = self._poll_request(request_url, auth)
        response.raise_for_status()

    def _poll_request(self, url, auth):
        count_failed = 1
        while count_failed <= 5:
            try:
                response = self._session.get(url, timeout=300, auth=auth, verify=False)
                if 200 <= response.status_code < 400:
                    print(f"_poll_request: STATUS_CODE = {response.status_code}")
                    return response
                else:
                    print(f"_poll_request: STATUS_CODE = {response.status_code}")
            except Exception as e:
                print(f"FAILED {count_failed}...........{str(e)}")

            count_failed += 1
            time.sleep(5)
        return None

    def _load_bio_config_from_sys_params(self):
        param_name = "seenpo_hr_attendance.bio_device_config"
        bio_config_str = self.env["ir.config_parameter"].sudo().get_param(param_name, default=False)

        if bio_config_str:
            arr = bio_config_str.split(",")
            if len(arr) > 2:
                self._bio_config["url"] = arr[0][:-len("/")] if arr[0].endswith("/") else arr[0]
                self._bio_config["username"] = arr[1]
                self._bio_config["password"] = arr[2]

    '''
    TODO: This is temporary method to run each time need to download/import all log from bio device into Odoo database.
    Before run this method, the related log data in Odoo DB need to be deleted to avoid duplication data  
    '''
    def _action_download_all_bio_log(self):
        try:
            import_start_date = datetime.datetime(2021, 6, 1)
            today = datetime.datetime.now()
            filename = today.strftime('%m%d%y') + '.txt'
            csv_directory = "./csv/"
            if not os.path.isdir(csv_directory):
                os.mkdir(csv_directory)

            while import_start_date < today:
                try:
                    import_end_date = import_start_date + relativedelta(months=1, days=-1)
                    info = f"DOWNLOAD - {import_start_date} - {import_end_date}"
                    file_content = bytes('', 'utf-8')

                    csv_filename = f"SUCCESS - {import_start_date.strftime('%Y%m%d')} - " \
                                   f"{import_end_date.strftime('%Y%m%d')}.csv"

                    if os.path.isfile(os.path.join(csv_directory, csv_filename)):
                        print(f"SKIPPED - because existing result")
                        import_start_date = import_end_date + datetime.timedelta(days=1)
                        continue

                    self._get_bio_data(import_start_date, import_end_date)
                    time.sleep(5)
                    response = self._download_bio_data(filename)
                    time.sleep(5)
                    if response.status_code == 200 and response.content:
                        # dict_content = csv.DictReader(response.text.splitlines())

                        info += f" - SUCCESS"
                        file_content = response.content

                    time.sleep(5)
                except Exception as e:
                    print("Exception general: " + str(e))
                    info += f" - FAILED"
                    csv_filename = f"FAILED - {import_start_date.strftime('%Y%m%d')} - " \
                                   f"{import_end_date.strftime('%Y%m%d')}.csv"
                    file_content = bytes(str(e), 'utf-8')

                import_start_date = import_end_date + datetime.timedelta(days=1)
                print(info)

                file_path = os.path.join(csv_directory, csv_filename)
                with open(file_path, mode="wb") as file:
                    file.write(file_content)

            return True

        except Exception as e:
            print("Exception general - _action_download_all_bio_log: " + str(e))
            return "There are errors while importing bio logs."

    '''
    TODO: This is temporary method to run each time need to import all log from bio device into Odoo database.
    Before run this method, the related log data in Odoo DB need to be deleted to avoid duplication data  
    '''
    def _action_import_all_bio_log_from_local_files(self, csv_directory):
        try:
            BioLog = self.env['seenpo.hr.attendance.bio.log']
            logs = BioLog.sudo().search([], limit=1)
            if logs:
                print("This action should be run at the first time bio log table just created and empty.")
                return

            if not csv_directory:
                csv_directory = "./csv/"
            csv_files = []
            for file in os.listdir(csv_directory):
                if file.endswith(".csv"):
                    csv_files.append(file)

            if not csv_files:
                print("Cannot found the csv files to import.")
                return

            for csv_file in csv_files:
                file_path = os.path.join(csv_directory, csv_file)
                info = f"IMPORT - {file_path}"

                create_vals_list = []

                with open(file_path, mode="r", encoding="utf8") as data:
                    dict_content = csv.DictReader(data)

                    if dict_content:
                        for row in dict_content:
                            user_id = row.get('User id')
                            card = row.get('Card No')
                            employee = row.get('Employee ID/ User Name')
                            check_in_date = datetime.datetime.strptime(row.get("Date"), "%m/%d/%Y")
                            first_in_time = row.get('First In Time')
                            last_out_time = row.get('Last Out Time')

                            create_vals_list.append({
                                "bio_user_id": user_id,
                                "card_number": card,
                                "employee": employee,
                                "check_in_date": check_in_date,
                                "first_in_time": first_in_time,
                                "last_out_time": last_out_time
                            })

                if create_vals_list:
                    BioLog.create(create_vals_list)
                    info += f" - SUCCESS - {len(create_vals_list)} records"
                else:
                    info += f" - EMPTY"

                print(info)

            return True

        except Exception as e:
            print("Exception general - _action_import_all_bio_log_from_local_files: " + str(e))
            return "There are errors while importing bio logs."

    # def _login_bio_web(self, username, password):
    #     LOGIN_URL = 'http://viet-toan.ddns.net:8081/'
    #     # SECURE_URL = 'https://the-internet.herokuapp.com/secure'
    #
    #     ACCESS_DATA = {
    #         'username': username,
    #         'password': password
    #     }
    #     auth = (username, password)
    #
    #     RESULT = requests.get(LOGIN_URL, timeout=1, auth=auth)
    #     # RESULT2 = requests.get(SECURE_URL)
    #     return RESULT.text