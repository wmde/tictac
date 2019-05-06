# -*- coding: utf-8 -*-
##############################################################################
#
#    TicTac allows several HR functionalities. This program bases on Odoo v. 8. Copyright
#    (C) 2018 ITIS www.itis.de commissioned by Wikimedia Deutschland e.V.
#
#    This program is free software: you can redistribute it and/or modify it under the
#    terms of the GNU Affero General Public License as published by the Free Software
#    Foundation, either version 3 of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT ANY
#    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
#    PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License along with
#    this program. If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "ITIS HR Attendance Extend",
    'summary': """ Module will extend HR Attendance""",
    'description': """
        Module to extend HR Attendance
    """,
    'author': "IT IS AG",
    'website': "http://www.itis-odoo.de",
    'category': 'base',
    'version': '1.0.55.0',
    'depends': ['hr_attendance', 'hr_timesheet', 'hr_timesheet_sheet'],
    'data': [
        'security/groups.xml',
        'views/hr_timesheet_sheet_view.xml',
        'views/itis_holiday_view.xml',
        'views/templates.xml',
        'views/hr_holiday_view.xml',
        'wizard/sign_in_task_view.xml',
        'wizard/hr_timesheet_overview_export.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/data.xml',
    ],
    'qweb': ['static/src/xml/templates.xml'],
    'css': [],
    'demo': [],
