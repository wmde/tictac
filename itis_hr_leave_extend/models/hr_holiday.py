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
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
from openerp.exceptions import Warning
import math
from openerp import SUPERUSER_ID


class HRHolidayTimesheet(models.Model):

    _name = "hr.holidays.timesheet"

    date = fields.Date('Date')
    holiday_id = fields.Many2one("hr.holidays", "Holiday")
    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet', 'Sheet')
    timesheet_id = fields.Many2one("hr.analytic.timesheet", "Timesheet")
    duration = fields.Float("Hours")

class HRTimesheetSheet(models.Model):

    _inherit = "hr_timesheet_sheet.sheet"

    @api.model
    def create(self, values):
        res = super(HRTimesheetSheet, self).create(values)
        res.calc_leave_hours()
        return res

    @api.multi
    def calc_leave_hours(self):
        leave_obj = self.env['hr.holidays']
        leave_recs = leave_obj.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'), ('state', '!=', 'refuse')])
        for leave in leave_recs:
            leave_processed = True
            for hl_ts_rec in leave.holidays_timesheet_ids:
                if not hl_ts_rec.timesheet_id:
                    #print"Calc leave hours - No Timesheet_id", hl_ts_rec
                    leave_processed = False
            if not leave_processed:
                leave.make_timesheet_entry()

class HRHoliday(models.Model):

    _inherit = "hr.holidays"

    holidays_timesheet_ids = fields.One2many("hr.holidays.timesheet", "holiday_id", "Timesheet")

    @api.multi
    def holidays_refuse(self):
        res = super(HRHoliday, self).holidays_refuse()
        for hl_ts_rec in self.sudo().holidays_timesheet_ids:
            hl_ts_rec.timesheet_id.unlink()
            hl_ts_rec.write({'sheet_id': False})
        return res

    @api.multi
    def holidays_validate(self):
        res = super(HRHoliday, self).holidays_validate()
        self.make_timesheet_entry()
        return res

    @api.multi
    def make_holidays_timesheet(self, res):
        result = []
        holi_ts_obj = self.env['hr.holidays.timesheet']
        cur_recs = holi_ts_obj.search([('holiday_id', '=', self.id)])
        res_days = res.keys()
        for rec in cur_recs:
            if rec.date not in res_days:
                rec.unlink()
        for day, duration in res.iteritems():
            holiday =  None
            holiday = self.env['itis.holiday'].search([('date', '=', day)])
            if holiday:
                continue
            cur_rec = holi_ts_obj.search([('holiday_id', '=', self.id), ('date', '=', day)])
            if not cur_rec.id:
                cur_rec = holi_ts_obj.create({'date': day, 'duration': duration, "holiday_id": self.id})
            if cur_rec.duration != duration:
                cur_rec.update({'duration': duration})
            result.append(cur_rec)
        return result

    @api.multi
    def make_timesheet_entry(self):
        res = self.count_day_hours_leave()
        res = self.make_holidays_timesheet(res)
        account_id = False
        if self.is_ot_leave:
            account_id = self.env.user.company_id.ot_leave_account_id
        else:
            account_id = self.env.user.company_id.leave_account_id
        if not account_id:
            raise Warning(_('Please set the analytic account for Leaves.\nPlease contact your administrator for the same.'))
        sheet_obj = self.env['hr_timesheet_sheet.sheet']
        timesheets = sheet_obj.search([("employee_id", '=', self.employee_id.id)])
        for hl_ts_rec in res:
            if hl_ts_rec.timesheet_id:
                continue
            cur_day = datetime.strptime(hl_ts_rec.date, DEFAULT_SERVER_DATE_FORMAT)
            for timesheet in timesheets:
                ts_date_from = datetime.strptime(timesheet.date_from, DEFAULT_SERVER_DATE_FORMAT)
                ts_date_to = datetime.strptime(timesheet.date_to, DEFAULT_SERVER_DATE_FORMAT)
                if cur_day >= ts_date_from and cur_day <= ts_date_to:
                    if timesheet.state != 'draft':
                        continue
                        #raise Warning(_('The Time period is allready closed. \n Please contact the Human Resource Team if the leave request should be confirmed nevertheless'))
                    #print"cur_day ", cur_day
                    ana_ts_id = self.create_timesheet(account_id, timesheet, hl_ts_rec.duration, hl_ts_rec.date)
                    hl_ts_rec.write({'timesheet_id': ana_ts_id[0], 'sheet_id': timesheet.id})
        return True

    @api.one
    def create_timesheet(self, account_id, sheet, duration, day):
        timesheet_obj = self.pool.get('hr.analytic.timesheet')
        cr = self.env.cr
        uid = self.env.uid
        emp_obj = self.env['hr.employee']
        hour = duration
        res = timesheet_obj.default_get(cr, uid, ['product_id','product_uom_id'])
        # res.update({
        #     'general_account_id': False,
        # })
        if not res['product_id']:
            res['product_id'] = 1
        if not res['product_uom_id']:
            res['product_uom_id'] = 5
        if not res['product_uom_id']:
            raise osv.except_osv(_('User Error!'), _('Please define cost unit for this employee.'))
        up = timesheet_obj.on_change_unit_amount(cr, uid, False, res['product_id'], hour,False, res['product_uom_id'])['value']
        print"UP ", up
        res['name'] = "Leave on " + day
        res['account_id'] = account_id.id
        res['unit_amount'] = hour
        emp_journal = emp_obj.search([('user_id', '=', self.employee_id.user_id.id)]).journal_id
        res['journal_id'] = emp_journal and emp_journal.id or False
        res.update(up)
        up = timesheet_obj.on_change_account_id(cr, uid, [], res['account_id']).get('value', {})
        res.update(up)
        print"RES ", res
        # if not res['general_account_id']:
        #     res['general_account_id'] = 698
        res.update({
            'date': day,
            'user_id': self.employee_id.user_id.id,
            'sheet_id': sheet.id,
        })
        return timesheet_obj.create(cr, SUPERUSER_ID, res)

    @api.multi
    def count_day_hours_leave(self):
        res = {}
        date_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATETIME_FORMAT)
        same_day = self.check_same_day(date_from, date_to)
        temp_date = date_from
        day_hours = 0.0
        weekday = temp_date.weekday()
        for contract in self.employee_id.contract_ids:
            cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)
            cont_end_date = False
            if not contract.date_end:
                if cont_start_date <= temp_date:
                    if same_day:
                        cur_hour = self.get_day_hours(date_from, contract.working_hours.attendance_ids)
                        day_hours = cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        if self.leave_selection =='half_day':
                           new_hour =new_hour/2
                        res.update({day_str: new_hour})
                    else:
                        fday_cur_hour = self.get_day_hours(date_from, contract.working_hours.attendance_ids)
                        day_hours += fday_cur_hour
                        lday_cur_hour = self.get_day_hours(date_to, contract.working_hours.attendance_ids)
                        day_hours = lday_cur_hour
                        fday_str = datetime.strftime(date_from, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        fday_new_hour = res.get(fday_str, 0.0) + fday_cur_hour
                        if self.leave_selection =='half_day':
                           fday_new_hour =fday_new_hour/2
                        res.update({fday_str: fday_new_hour})
                        lday_str = datetime.strftime(date_to, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        lday_new_hour = res.get(lday_str, 0.0) + lday_cur_hour
                        if self.leave_selection_date_to =='half_day':
                           lday_new_hour =lday_new_hour/2
                        #if temp_date == self.start_date and self.start_date_leave_selection == 'half_day':
                        #   lday_new_hour =lday_new_hour/2
                        #elif temp_date == self.end_date and self.end_date_leave_selection == 'half_day':
                        #   lday_new_hour =lday_new_hour/2
                        res.update({lday_str: lday_new_hour})
            else:
                cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
                cont_end_date += timedelta(days=1)
                if cont_start_date <= temp_date and cont_end_date >= temp_date:
                    if same_day:
                        cur_hour = self.get_day_hours(date_from, contract.working_hours.attendance_ids)
                        day_hours += cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        if self.leave_selection =='half_day':
                           new_hour =new_hour/2
                        res.update({day_str: new_hour})
                    else:
                        fday_cur_hour = self.get_day_hours(date_from, contract.working_hours.attendance_ids)
                        day_hours += fday_cur_hour
                        lday_cur_hour = self.get_day_hours(date_to, contract.working_hours.attendance_ids)
                        day_hours = lday_cur_hour
                        fday_str = datetime.strftime(date_from, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        fday_new_hour = res.get(fday_str, 0.0) + fday_cur_hour
                        if self.leave_selection =='half_day':
                           fday_new_hour =fday_new_hour/2
                        res.update({fday_str: fday_new_hour})
                        lday_str = datetime.strftime(date_to, DEFAULT_SERVER_DATETIME_FORMAT).split(" ")[0]
                        lday_new_hour = res.get(lday_str, 0.0) + lday_cur_hour
                        if self.leave_selection_date_to =='half_day':
                           lday_new_hour =lday_new_hour/2
                        res.update({lday_str: lday_new_hour})
        date_from = datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(self.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
        temp_date = date_from
        temp_date += timedelta(days=1)
        while temp_date < date_to:
            weekday = temp_date.weekday()
            for contract in self.employee_id.contract_ids:
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
#                     cont_end_date += timedelta(days=1)
                    if cont_start_date <= temp_date and cont_end_date >= temp_date:
                        cur_hour = self.get_hours(weekday, contract.working_hours.attendance_ids)
                        day_hours = cur_hour
                        day_str = datetime.strftime(temp_date, DEFAULT_SERVER_DATE_FORMAT).split(" ")[0]
                        new_hour = res.get(day_str, 0.0) + cur_hour
                        res.update({day_str: new_hour})

            temp_date += timedelta(days=1)
        return res

    @api.onchange("number_of_days_temp","leave_selection","leave_selection_date_to")
    def calc_days(self):
        res = 0
        if not self.date_from or not self.date_to:
            return {}
        date_from = datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(self.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
        # if date_from == date_to:
        #     if self.leave_selection =='half_day' or self.leave_selection_date_to =='half_day':
        #         self.number_of_days_temp = 0.5
        #         return {}
        temp_date = date_from
        while temp_date <= date_to:
            holiday =  None
            holiday = self.env['itis.holiday'].search([('date', '=', temp_date)])
            if holiday:
                temp_date += timedelta(days=1)
                continue
            weekday = temp_date.weekday()
            for contract in self.employee_id.contract_ids:
                cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)
                cont_end_date = False
                if not contract.date_end:
                    if cont_start_date <= temp_date:
                        if self.get_hours(weekday, contract.working_hours.attendance_ids) > 0.0:
                            if temp_date == date_from and self.leave_selection =='half_day':
                                res += 0.25
                                break
                            if temp_date == date_to and self.leave_selection_date_to =='half_day':
                                res += 0.25
                                break
                            res += 1
                else:
                    cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
#                     cont_end_date += timedelta(days=1)
                    if cont_start_date <= temp_date and cont_end_date >= temp_date:
                        if self.get_hours(weekday, contract.working_hours.attendance_ids) > 0.0:
                            if temp_date == date_from and self.leave_selection =='half_day':
                                res += 0.25
                                break
                            if temp_date == date_to and self.leave_selection_date_to =='half_day':
                                res += 0.25
                                break
                            res += 1
            temp_date += timedelta(days=1)
        self.number_of_days_temp = res
        return {}

class HRHolidayStatus(models.Model):

    _inherit = "hr.holidays.status"

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not context.get('employee_id',False):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HRHolidayStatus, self).name_get(cr, uid, ids, context=context)

        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if not record.limit:
                name = name
            res.append((record.id, name))
        return res
