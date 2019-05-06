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

from openerp import models, api, fields, _

class employee_meeting(models.Model):

    _name = 'employee.meeting'
    _rec_name = 'meeting_date'

    name = fields.Char(string="Name")
    meeting_date = fields.Date(string="Meeting Date")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    supervisor_id = fields.Many2one('hr.employee',string="Supervisor")
    note = fields.Char(string="Meeting Notes")


class employee_instruction(models.Model):

    _name = 'employee.instruction'
    _rec_name = 'meeting_date'

    name = fields.Char(string="Name")
    meeting_date = fields.Date(string="Meeting Date")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    supervisor_id = fields.Many2one('hr.employee',string="Supervisor")
    note = fields.Char(string="Meeting Notes")
