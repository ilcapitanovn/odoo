# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Việt Toản Attendances Bio History",
    "version": "15.0.0.1.0",
    "author": "Tuan Huynh, " "Odoo Community Association (OCA)",
    "category": 'Human Resources/Seenpo Attendances',
    "website": "https://github.com/OCA/",
    "license": "AGPL-3",
    "depends": ['base', 'hr'],
    "data": [
        "security/seenpo_hr_attendance_security.xml",
        "security/ir.model.access.csv",
        "views/seenpo_hr_attendance_bio_log_views.xml",
        "views/hr_employee_views.xml",
        "wizard/wizard_hr_attendance_report.xml",
        "report/seenpo_hr_attendance_timesheet_report.xml",
        "report/seenpo_hr_attendance_annual_leave_report.xml",
        "views/seenpo_hr_attendance_menu.xml",
    ],
    "assets": {
        'web.assets_backend': [
            'seenpo_hr_attendance/static/src/scss/seenpo_hr_attendance.scss',
            'seenpo_hr_attendance/static/src/js/button_refresh_bio_log.js'
        ],
        'web.assets_qweb': [
            'seenpo_hr_attendance/static/src/xml/button_refresh_bio_log.xml'
        ]
    },
    "installable": True,
    'application': True,
}
