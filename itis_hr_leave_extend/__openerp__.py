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
    'name': "ITIS HR Leave Extend",
    'summary': """ Module will extend Human Ressources leave""",
    'description': """
        Module to extend the functionalities of the HR module.
    """,
    'author': "IT IS AG",
    'website': "http://www.itis-odoo.de",
    'category': 'base',
    'version': '1.0.55.0',
    'depends': ['itis_hr_extend','itis_hr_attendance_extend'],
    'data': [
        'views/hr_setting_view.xml',
        'security/ir.model.access.csv',
        'wizard/hr_sick_leave.xml'
    ],
    'css': [],
    'demo': [],
