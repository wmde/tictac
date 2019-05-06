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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class OTChange(models.TransientModel):

    _name = "ot.change"

    reason = fields.Char("Reason")
    ot_time = fields.Float("Overtime Count")
    leave_day = fields.Float("Leave Day")

    @api.model
    def default_get(self, fields):

        res = super(OTChange, self).default_get(fields)
        emp_id = self.env.context.get("active_id")
        emp_rec = self.env['hr.employee'].browse(emp_id)
        if self.env.context.get("from_ot_change", False):
            # res.update({'ot_time': emp_rec.overtime_count})
            res.update({'ot_time': emp_rec.employee_overtime_id.emp_overtime_count})
        else:
            res.update({'leave_day': emp_rec.additional_leave_days})
        return res

    @api.multi
    def set_ot_time(self):
        emp_id = self.env.context.get("active_id")
        emp_rec = self.env['hr.employee'].browse(emp_id)
        if self.env.context.get("from_ot_change", False):
            emp_rec.update_overtime_count(self.ot_time, self.reason)
        else:
            emp_rec.update_leave_day(self.leave_day, self.reason)
        return True

class LDChange(models.TransientModel):

    _name = "ld.change"

    reason = fields.Char("Reason")
    type = fields.Selection([('add', 'Hinzufügen'),('sub', 'Abziehen')], "Type")
    leave_day = fields.Float("Leave Day")

    @api.multi
    def set_ld_time(self):
        leave_journal_obj = self.env['hr.leave.journal']
        leave_days = self.leave_day
        if self.type == 'sub':
            leave_days = leave_days * -1
        values = {
            'employee_id': self.env.context.get("active_id"),
            'year': datetime.today().year,
            'year_type': 'actual',
            'type': 'manual',
            'leave_type':'days',
            'leave_days': leave_days,
            'name': self.reason + ' ' + self.env['res.users'].browse(self._uid).name + ' ' + datetime.now().strftime('%d%m%Y %H:%M:%S'),
        }
        leave_journal_obj.create(values)

    #for SOW17
    @api.multi
    def set_nextyear_ld_time(self):
        """Add a logic to give ability to change leave day for the next year.
            User can only change it after May month
        """
        leave_journal_obj = self.env['hr.leave.journal']
        leave_days = self.leave_day
        if self.type == 'sub':
            leave_days = leave_days * -1
        values = {
            'employee_id': self.env.context.get("active_id"),
            'year': datetime.today().year+1,
            'year_type': 'next',
            'type': 'manual',
            'leave_type':'days',
            'leave_days': leave_days,
            'name': self.reason + ' ' + self.env['res.users'].browse(self._uid).name + ' ' + datetime.now().strftime('%d%m%Y %H:%M:%S'),
        }
        leave_journal_obj.create(values)
