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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class ITISHoliday(models.Model):

    _name = "itis.holiday"

    name = fields.Char("Holiday Name")
    date = fields.Date("Date")

    @api.model
    def get_holiday_date(self):
        """
        function call from the js, use to return the holiday dates
        """
        holiday_dates = []
        for holiday_brw in self.search([]):
            holiday_dates.append(holiday_brw.date)

        return holiday_dates

    @api.model
    def create(self, values):
        """
        To create holiday list entry calender of leave request

        """
        res = super(ITISHoliday, self).create(values)
        if values:
            holiday_date = values.get('date')
            holiday_name = values.get('name')

            if holiday_date and holiday_name:
                hr_holidays_status_brw = self.env['hr.holidays.status'].search([('is_holiday','=',True)],limit=1)
                hr_holidays_env = self.env['hr.holidays']
                if hr_holidays_status_brw:
                    hr_emp_records = self.env['hr.employee'].search([('user_id','!=',None)])
                    for hr_emp_brw in hr_emp_records:
                        try:
                            hr_holiday_brw = hr_holidays_env.with_context(mail_notify_force_send=False,holiday_create=True,mail_create_nosubscribe=False,mail_create_nolog=False).\
                                create({'employee_id':hr_emp_brw.id, 'date_from':holiday_date,'date_to':holiday_date,
                                                                     'holiday_name':holiday_name,'holiday_status_id':hr_holidays_status_brw.id,
                                                                    'holiday_type':'employee','leave_selection':'full_day','leave_selection_date_to':'full_day',})
                            # msg = _("Holiday %s created.") %(holiday_name)
                            # hr_holiday_brw.message_post(body=msg)
                            self._cr.execute("update hr_holidays set state = 'validate' where id = %s",(hr_holiday_brw.id,))
                        except:
                            #Todo Error handling
                            pass
        return res

    @api.multi
    def unlink(self):
        """
        To delete the related holiday from the leave request
        """
        for itis_holiday_brw in self:
            hr_holidays_env = self.env['hr.holidays']
            hr_holidays_records = hr_holidays_env.search([('date_from','=',itis_holiday_brw.date),('holiday_name','=',itis_holiday_brw.name)])
            for hr_holiday_brw in hr_holidays_records:
                self._cr.execute("delete from hr_holidays where id = %s",(hr_holiday_brw.id,))

        return super(ITISHoliday, self).unlink()

    @api.multi
    def write(self, vals):
        """
        To write on the leave request holiday base upon the conditions
        """
        hr_holidays_status_brw = self.env['hr.holidays.status'].search([('is_holiday','=',True)],limit=1)
        hr_holidays_env = self.env['hr.holidays']
        if vals.get('date'):

            hr_holidays_records = hr_holidays_env.search([('date_from','=',self.date),('holiday_name','=',self.name)])
            for hr_holiday_brw in hr_holidays_records:
                self._cr.execute("delete from hr_holidays where id = %s",(hr_holiday_brw.id,))
            if vals.get('name'):
                name = vals.get('name')
            else:
                name = self.name
            if hr_holidays_status_brw:
                hr_emp_records = self.env['hr.employee'].search([('user_id','!=',None)])
                for hr_emp_brw in hr_emp_records:
                    hr_holiday_brw = hr_holidays_env.create({'employee_id':hr_emp_brw.id,'date_from':vals.get('date'),'date_to':vals.get('date'),'holiday_name':name,'holiday_status_id':hr_holidays_status_brw.id})
                    # msg = _("Holiday %s created.") %(name)
                    # hr_holiday_brw.message_post(body=msg)
                    self._cr.execute("update hr_holidays set state = 'validate' where id = %s",(hr_holiday_brw.id,))
        elif vals.get('name') and not  vals.get('date'):
            hr_holidays_records = hr_holidays_env.search([('date_from','=',self.date),('holiday_name','=',self.name)])
            for hr_holidays_brw in hr_holidays_records:
                self._cr.execute("update hr_holidays set holiday_name = %s where id = %s" , (vals.get('name'),hr_holidays_brw.id))
        res = super(ITISHoliday, self).write(vals)
        return res
