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
    'name': "ITIS HR Extend",
    'summary': """ Module will extend Human Ressources""",
    'description': """
        Module to extend the functionalities of the HR module.
        Employee new fields and views
        Timesheet extensions
        Day Off Workflow
        Reporting
    """,
    'author': "IT IS AG",
    'website': "http://www.itis-odoo.de",
    'category': 'base',
    'version': '1.0.55.0',
    'depends': ['hr','hr_contract', 'hr_holidays', 'hr_payroll', 'resource'],
    'data': [
        'security/groups.xml',
        'static/data.xml',
        'views/employee_meeting_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_holiday_view.xml',
        'views/fte_report_view.xml',
        'views/employee_report_view.xml',
        'views/employee_payroll_report_view.xml',
        'wizard/ot_change_view.xml',
        'wizard/fte_wizard_view.xml',
        'wizard/emp_payroll_wizard_view.xml',
        'wizard/emp_data_wizard_view.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/data.xml',
        ],
    'css': [],
    'demo': [],
