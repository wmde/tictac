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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from dateutil.relativedelta import relativedelta

class hr_sick_leave(models.TransientModel):

    _name = 'hr.sick.leave'

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')


    @api.multi
    def confirm_sick_time(self):
        """ This function is use to fill the timesheet when employee is sick.
        """
        hr_employee_env = self.env['hr.employee']
        sheet_obj = self.env['hr_timesheet_sheet.sheet']
        timesheet_obj = self.pool.get('hr.analytic.timesheet')
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            account_id = self.env.user.company_id and self.env.user.company_id.sick_account_id or False
            if not account_id:
                raise Warning(_('Please set the analytic account for Sick Leaves.\nPlease contact your administrator for the same.'))

            for hr_employee_brw in hr_employee_env.browse(active_ids):
                res = self.count_day_sickleave(hr_employee_brw)
                timesheets = sheet_obj.search([("employee_id", '=', hr_employee_brw.id)])
                #for sick_leave_rec in res:
                for key, value in res.iteritems():
                    cur_day_timesheeht_found = False
                    cur_day = datetime.strptime(key, DEFAULT_SERVER_DATE_FORMAT)
                    for timesheet in timesheets:
                        ts_date_from = datetime.strptime(timesheet.date_from, DEFAULT_SERVER_DATE_FORMAT)
                        ts_date_to = datetime.strptime(timesheet.date_to, DEFAULT_SERVER_DATE_FORMAT)
                        if cur_day >= ts_date_from and cur_day <= ts_date_to:
                            cur_day_timesheeht_found = True
                            # print"Final Timesheet----",timesheet
                            # if timesheet.state != 'draft':
                            #   raise Warning(_('The Time period is allready closed. \n Please contact the Human Resource Team if the leave request should be confirmed nevertheless'))
                            # timesheet_ids = timesheet_obj.search(self.env.cr,self.env.uid,[('name','like','Sick Leave on:'),('sheet_id','=',timesheet.id),('user_id','=',hr_employee_brw.user_id.id)])
                            # if timesheet_ids:
                            #     timesheet_obj.unlink(self.env.cr,self.env.uid,timesheet_ids)
                            ana_ts_id = self.create_sickleave_timesheet(account_id, timesheet, value, key,hr_employee_brw)
                            #hl_ts_rec.write({'timesheet_id': ana_ts_id[0], 'sheet_id': timesheet.id})
                    if cur_day_timesheeht_found == False:
                        self.create_future_timesheet(cur_day,account_id, value, key,hr_employee_brw)

        return True

    def create_future_timesheet(self,cur_day,account_id, value, key,hr_employee_brw):
        """
        Use to create a future timesheet base upon the user configuration

        """
        hr_timesheet =self.env['hr_timesheet_sheet.sheet']
        timesheet_start_date = self.get_timesheet_start_date(cur_day)
        timesheet_end_date =self.get_timesheet_end_date(cur_day)

        timesheets = hr_timesheet.search([("employee_id", '=', hr_employee_brw.id),("date_from", '=', timesheet_start_date),("date_to", '=', timesheet_end_date)])
        # print"START----------END--------",timesheet_start_date,timesheet_end_date,timesheets
        if not timesheets:
            timesheets = hr_timesheet.create({'employee_id':hr_employee_brw.id,'date_from':timesheet_start_date,'date_to':timesheet_end_date})

        self.create_sickleave_timesheet(account_id, timesheets, value, key,hr_employee_brw)

    def get_timesheet_start_date(self,cur_day):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            timesheet_start_date = cur_day.strftime('%Y-%m-01')
        elif r == 'week':
            timesheet_start_date = (cur_day+ relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif r == 'year':
            timesheet_start_date = cur_day.strftime('%Y-01-01')
        else:
            timesheet_start_date = cur_day
        return timesheet_start_date

    def get_timesheet_end_date(self,cur_day):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            timesheet_end_date = (cur_day+ relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif r == 'week':
            timesheet_end_date = (cur_day+ relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r == 'year':
            timesheet_end_date = cur_day.strftime('%Y-12-31')
        else:
            timesheet_end_date = cur_day
        return timesheet_end_date


    @api.one
    def create_sickleave_timesheet(self, account_id, sheet, duration, day,hr_employee_brw):
        """
        This function is use to create analytic timesheet based on the sick date and other inputs
        :param account_id: analytic account id
        :param sheet: timesheet id
        :param duration: planned time of the leave
        :param day: date of the leave
        :param hr_employee_brw: employee browse record
        :return: created record for the analytic timesheet
        """
        timesheet_obj = self.pool.get('hr.analytic.timesheet')
        cr = self.env.cr
        uid = self.env.uid
        emp_obj = self.env['hr.employee']
        hour = duration

        res = timesheet_obj.default_get(cr, uid, ['product_id','product_uom_id'])

        if not res['product_uom_id']:
            raise Warning(_('User Error! \nPlease define cost unit for this employee.'))
        up = timesheet_obj.on_change_unit_amount(cr, uid, False, res['product_id'], hour,False, res['product_uom_id'])['value']

        res['name'] = "Sick Leave on:" + day
        res['account_id'] = account_id.id
        res['unit_amount'] = hour
        emp_journal = emp_obj.search([('user_id', '=', hr_employee_brw.user_id.id)]).journal_id
        res['journal_id'] = emp_journal and emp_journal.id or False
        res.update(up)
        up = timesheet_obj.on_change_account_id(cr, uid, [], res['account_id']).get('value', {})
        res.update(up)
        res.update({
            'date': day,
            'user_id': hr_employee_brw.user_id.id,
            'sheet_id': sheet.id,
        })
        return timesheet_obj.create(cr, SUPERUSER_ID, res)






    def count_day_sickleave(self,hr_employee_brw):
        res = {}
        date_from = datetime.strptime(self.start_date, DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = datetime.strptime(self.end_date, DEFAULT_SERVER_DATETIME_FORMAT)
        same_day = self.check_same_day(date_from, date_to)
        temp_date = date_from
        day_hours = 0.0
        weekday = temp_date.weekday()
        for contract in hr_employee_brw.contract_ids:
            cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)

            if not contract.date_end:
                if cont_start_date <= temp_date:
                    if same_day:
                        cur_hour = self.get_sameday_hours(date_from, date_to, contract.working_hours.attendance_ids)
                        day_hours += cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        res.update({day_str: new_hour})
                    else:
                        fday_cur_hour = self.get_fday_hours(date_from, contract.working_hours.attendance_ids)
                        day_hours += fday_cur_hour
                        lday_cur_hour = self.get_lday_hours(date_to, contract.working_hours.attendance_ids)
                        day_hours += lday_cur_hour
                        fday_str = datetime.strftime(date_from, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        fday_new_hour = res.get(fday_str, 0.0) + fday_cur_hour
                        res.update({fday_str: fday_new_hour})
                        lday_str = datetime.strftime(date_to, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        lday_new_hour = res.get(lday_str, 0.0) + lday_cur_hour
                        res.update({lday_str: lday_new_hour})
            else:
                cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
                cont_end_date += timedelta(days=1)
                if cont_start_date <= temp_date and cont_end_date >= temp_date:
                    if same_day:
                        cur_hour = self.get_sameday_hours(date_from, date_to, contract.working_hours.attendance_ids)
                        day_hours += cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        res.update({day_str: new_hour})
                    else:
                        fday_cur_hour = self.get_fday_hours(date_from, contract.working_hours.attendance_ids)
                        day_hours += fday_cur_hour
                        lday_cur_hour = self.get_lday_hours(date_to, contract.working_hours.attendance_ids)
                        day_hours += lday_cur_hour
                        fday_str = datetime.strftime(date_from, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        fday_new_hour = res.get(fday_str, 0.0) + fday_cur_hour
                        res.update({fday_str: fday_new_hour})
                        lday_str = datetime.strftime(date_to, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        lday_new_hour = res.get(lday_str, 0.0) + lday_cur_hour
                        res.update({lday_str: lday_new_hour})
        date_from = datetime.strptime(self.start_date.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(self.end_date.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
        temp_date = date_from
        temp_date += timedelta(days=1)
        while temp_date < date_to:
            weekday = temp_date.weekday()
            for contract in hr_employee_brw.contract_ids:
                cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)
                cont_end_date = False
                if not contract.date_end:
                    if cont_start_date <= temp_date:
                        cur_hour = self.get_hours(weekday, contract.working_hours.attendance_ids)
                        day_hours += cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATE_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        res.update({day_str: new_hour})
                else:
                    cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
                    if cont_start_date <= temp_date and cont_end_date >= temp_date:
                        cur_hour = self.get_hours(weekday, contract.working_hours.attendance_ids)
                        day_hours += cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATE_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        res.update({day_str: new_hour})

            temp_date += timedelta(days=1)

        return res


    def check_same_day(self, date_from, date_to):
        return date_from.date() == date_to.date()

    def get_sameday_hours(self, date_from, date_to, atten_ids):

        weekday = date_from.weekday()
        res = self.get_hours(weekday, atten_ids)
        return res

    def get_lday_hours(self, date_to, atten_ids):
        weekday = date_to.weekday()
        return self.get_hours(weekday, atten_ids)


    def get_fday_hours(self, date_from, atten_ids):
        weekday = date_from.weekday()
        return self.get_hours(weekday, atten_ids)


    def get_hours(self, weekday, atten_ids):
        res = 0.0
        for atten in atten_ids:
            if int(atten.dayofweek) == weekday:
                res += atten.hour_to - atten.hour_from
        return res













