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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp.exceptions import Warning
from openerp.http import request
import logging
logger = logging.getLogger(__name__)


class HRTimesheetSheet(models.Model):

    _inherit = "hr_timesheet_sheet.sheet"

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """To display the functional field value in the group by"""
        res = super(HRTimesheetSheet, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'total_timesheet' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    inv_value = 0.0
                    for line2 in lines:
                        inv_value += line2.total_timesheet
                    line['total_timesheet'] = inv_value
        if 'total_contract_time' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    inv_value = 0.0
                    for line2 in lines:
                        inv_value += line2.total_contract_time
                    line['total_contract_time'] = inv_value
        if 'time_diff' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    inv_value = 0.0
                    for line2 in lines:
                        inv_value += line2.time_diff
                    line['time_diff'] = inv_value
        return res

    @api.multi
    def write(self, vals):
        res = super(HRTimesheetSheet, self).write(vals)

        if 'timesheet_ids2' in vals:
            for timesheet_value in vals['timesheet_ids2']:
                if timesheet_value[2]:
                    date = timesheet_value[2].get('date')
                    if not date or (date>=self.date_from and date<=self.date_to):
                        pass
                    else:
                        raise Warning(_("Date should be between timesheet date."))

        return res

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        return [(r['id'], datetime.strptime(r['date_from'], '%Y-%m-%d').strftime('%d-%m-%Y')) \
                for r in self.read(cr, uid, ids, ['date_from'],
                    context=context, load='_classic_write')]

    @api.multi
    def get_analytic_timesheet_data(self):
        """
        This function is call from the Javascript
        """
        data_dict = {}
        data_list_new =[]
        if self and self.timesheet_ids:
            for timesheet_record in self.timesheet_ids:
                data_list =[]
                data_list_new.append(timesheet_record)
                data_list.append(timesheet_record.service_desc_id and timesheet_record.service_desc_id.name or False)
                data_list.append(timesheet_record.emp_comment)
                data_dict[timesheet_record.account_id.id] =data_list
        return data_dict


    @api.model
    def create_daily_timesheet(self):
        """
        Scheduler, use to create daily timesheet for the all employee
        """
        # print"In daily timesheet create scheduler---"
        today_date = datetime.now()
        for employee_brw in  self.env['hr.employee'].search([('user_id','!=',False)]):
            emp_contract_record =self.env['hr.contract'].search([("employee_id", '=', employee_brw.id),("date_start", '<=', today_date),'|',("date_end", '>=', today_date),("date_end", '=', False)])
            if emp_contract_record:
                timesheets = self.search([("employee_id", '=', employee_brw.id),("date_from", '<=', today_date),("date_to", '>=', today_date)])
                if not timesheets:
                    values = {'employee_id':employee_brw.id,
                              'date_from':today_date,
                              'date_to':today_date
                            }
                    try:
                        self.create(values)
                    except:
                        #Todo Error handling
                        pass

    @api.model
    def create_missingdate_timesheet(self):
        """
        Scheduler, use to create missing date timesheet for the all employee
        DATE NEED TO PROVIDED HERE.
        """
        print"In create_missingdate_timesheet---"
        # today_date = datetime.now()
        provided_dates = [datetime.strptime("2017-09-09 00:00:00",'%Y-%m-%d %H:%M:%S'),datetime.strptime("2017-09-10 00:00:00",'%Y-%m-%d %H:%M:%S')]
        for date in provided_dates:
            for employee_brw in  self.env['hr.employee'].search([('user_id','!=',False)]):
                emp_contract_record =self.env['hr.contract'].search([("employee_id", '=', employee_brw.id),("date_start", '<=', date),'|',("date_end", '>=', date),("date_end", '=', False)])
                if emp_contract_record:
                    timesheets = self.search([("employee_id", '=', employee_brw.id),("date_from", '<=', date),("date_to", '>=', date)])
                    if not timesheets:
                        values = {'employee_id':employee_brw.id,
                                  'date_from':date,
                                  'date_to':date
                                }
                        try:
                            print"timesheet create----",employee_brw
                            self.create(values)
                        except:
                            #Todo Error handling
                            pass

    def check_employee_attendance_state(self, cr, uid, sheet_id, context=None):
        ids_signin = self.pool.get('hr.attendance').search(cr,uid,[('sheet_id', '=', sheet_id),('action','=','sign_in')])
        ids_signout = self.pool.get('hr.attendance').search(cr,uid,[('sheet_id', '=', sheet_id),('action','=','sign_out')])

        if len(ids_signin) != len(ids_signout):
            logger.info("--Sign in, Sign out not equal timesheet ids--%s" %sheet_id)
            # raise osv.except_osv(('Warning!'),_('The timesheet cannot be validated as it does not contain an equal number of sign ins and sign outs.'))
        return True

    @api.model
    def automatic_sign_out(self):
        """
        Scheduler, Use to sign out the employee which are not sign out
        """
        logger.info("--In automatic_sign_out scheduler--")
        today_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cron_record = self.env['ir.cron'].search([('function','=','automatic_sign_out')],limit=1)
        if cron_record:
            cron_date = datetime.strptime(cron_record.nextcall,'%Y-%m-%d %H:%M:%S').date()
        else:
            cron_date = datetime.now().date()
        logger.info("--Date of the scheduler--%s"%(cron_date))
        hr_attendance = self.env['hr.attendance']
        for employee_brw in  self.env['hr.employee'].search([('user_id','!=',False)]):
            # timesheets = self.search([("employee_id", '=', employee_brw.id),("date_from", '<=', today_date),("date_to", '>=', today_date)],limit=1)
            timesheets = self.search([("employee_id", '=', employee_brw.id),("date_from", '=', cron_date)],limit=1)
            today_hr_attendance_ids = []
            if timesheets:
                today_hr_attendance_ids = [x.id for x in timesheets.attendances_ids]
                # today_date = datetime.now().date().strftime('%Y-%m-%d')
                # hr_attendance_records = hr_attendance.search([("employee_id", '=', employee_brw.id),('sheet_id','=',timesheets[0].id)])
                # for hr_attendance_record in hr_attendance_records:
                #     date_new = datetime.strptime(hr_attendance_record.name,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                #     if date_new == today_date:
                #         today_hr_attendance_ids.append(hr_attendance_record.id)
            if today_hr_attendance_ids:
                today_hr_attendance_ids.sort(reverse=True)
                if hr_attendance.browse(today_hr_attendance_ids[0]).action=='sign_in':
                    logger.info("--Automatically sign out employee %s" %employee_brw)
                    hr_attendance.create({'employee_id':employee_brw.id,'sheet_id':timesheets[0].id,'action':'sign_out','name':today_date})
                    self.send_sign_out_email(employee_brw)

    def send_sign_out_email(self,employee_brw):
        """
        This function is use to send a email to the user for automatic sign out
        """

        if employee_brw and employee_brw.user_id:
            email_to = False
            if employee_brw.work_email:
                email_to = employee_brw.work_email
            elif employee_brw.user_id.partner_id and employee_brw.user_id.partner_id.email:
                email_to = employee_brw.user_id.partner_id.email

            if email_to:
                ir_mail_env = self.env['ir.mail_server']
                active_outgoing_mail_server = ir_mail_env.search([('id','!=',False)], limit=1)
                email_vals = { }

                body_html= """
                                <p>
                                    Hallo """+str(employee_brw.name) +""",
                                </p>
                                <p>
                                    Sie wurden automatisch von TicTac abgemeldet. Bitte passen Sie ihr Timesheet an.
                                </p>
                                <p>
                                    Vielen Dank ihr HR Team.
                                </p>
                                """

                email_vals['email_from'] = employee_brw.company_id and employee_brw.company_id.email or 'info@yourcompany.example.com'
                email_vals['email_to'] =   email_to
                email_vals['subject'] = 'Automatic Sign Out'
                email_vals['body_html'] = body_html
                # if active_outgoing_mail_server:
                #     email_vals['mail_server_id'] = active_outgoing_mail_server.id
                mail = self.env['mail.mail'].create(email_vals)
                mail.send()
                logger.info("--Sign out email send.")


    @api.multi
    def action_set_to_draft(self):
        res = super(HRTimesheetSheet, self).action_set_to_draft()
        #newovertime
        overtime_count = self.employee_id.employee_overtime_id.emp_overtime_count - self.time_diff
        self.employee_id.employee_overtime_id.write({'emp_overtime_count': overtime_count})
        # overtime_count = self.employee_id.overtime_count - self.time_diff
        # self.employee_id.write({'overtime_count': overtime_count})
        return res

    @api.one
    def action_cancel(self):
        #newovertime
        overtime_count = self.employee_id.employee_overtime_id.emp_overtime_count - self.time_diff
        self.employee_id.employee_overtime_id.write({'emp_overtime_count': overtime_count})
        # overtime_count = self.employee_id.overtime_count - self.time_diff
        # self.employee_id.write({'overtime_count': overtime_count})
        self.write({'state': 'draft'})
        return True

    @api.multi
    def button_confirm(self):

        res = super(HRTimesheetSheet, self).button_confirm()
        #newovertime
        new_overtime = self.employee_id.employee_overtime_id.emp_overtime_count + self.time_diff
        self.employee_id.employee_overtime_id.write({'emp_overtime_count': new_overtime})
        # new_overtime = self.employee_id.overtime_count + self.time_diff
        # self.pool.get('hr.employee').write(self._cr,SUPERUSER_ID,self.employee_id.id,{'overtime_count': new_overtime})
        #self.employee_id.write({'overtime_count': new_overtime})
        self.write({'state': 'confirm'})
        return res

    @api.model
    def create(self, values):
        #cr, uid, context = self.env.cr, self.env.uid, self.env.context
        res_users_obj = self.env["res.users"]
        ir_model_obj = self.env["ir.model.data"]
        res_user_data = res_users_obj.browse([self.env.uid])
        xml_list = []
        group_ids = []
        for group in res_user_data.groups_id:
             group_ids.append(group.id)
        model_data = ir_model_obj.search([['model','=','res.groups'],['res_id','in',group_ids]])
        #model_data = ir_model_obj.browse(cr,uid,model_ids,context)
        for value in model_data:
            xml_list.append(value.name)
        if "group_hr_manager" in xml_list or "group_hr_payroll_manager" in xml_list or "group_hr_user" in xml_list or self.env.uid == 1:
            if 'date_from' in values and 'date_to' in values and values['date_from'] != values['date_to']:
                raise Warning(_("Start date and end date have to be the same day."))
            if 'date_from' in values and 'date_to' in values and 'employee_id' in values and self.search([('employee_id','=',values['employee_id']),('date_from','<=',values['date_from']),('date_to','>=',values['date_from'])]):
                raise Warning(_("You can only create one timesheet each day."))
            res = super(HRTimesheetSheet, self).create(values)
            res.calc_planned_hours()
            res.calc_leave_hours()
            return res
        else:
            raise Warning(_("You do not have pemission to create timesheets!"))

    @api.one
    def cal_tot_cont_time(self):
        total_duration = 0.0
        for pln_hrs in self.planned_ids:
            total_duration += pln_hrs.duration
        self.total_contract_time = total_duration
        self.time_diff = self.total_timesheet - self.total_contract_time
        return True

    @api.one
    def cal_total_hours(self):
        total_duration = 0.0
        for pln_hrs in self.planned_ids:
            total_duration += pln_hrs.duration
        self.total_timesheet_hours = self.total_timesheet
        self.total_planned_hours = total_duration
        self.overtime_hours = self.total_timesheet_hours - self.total_planned_hours


    @api.multi
    def fetch_holiday_list(self):
        res = []
        for hld in self.env["itis.holiday"].search([]):
            res.append(hld.date)
        return res

    @api.model
    def close_timesheet(self):
        for timesheet in self.search([('date_to','<',datetime.today().date().replace(day=1)),('state','=','draft')]):
            timesheet.button_confirm()
        return

    @api.one
    def calc_planned_hours(self):
        res = {}
        hld_list = self.fetch_holiday_list()
        date_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)
        temp_date = date_from
        while temp_date <= date_to:
            weekday = temp_date.weekday()
            day_hours = 0.0
            if datetime.strftime(temp_date, DEFAULT_SERVER_DATE_FORMAT) in hld_list:
                res.update({temp_date:day_hours})
                temp_date += timedelta(days=1)
                continue
            # contract_ids = self.pool.get('hr.contract').search(self._cr, SUPERUSER_ID, [('employee_id','=',self.id)])
            # contract_ids = self.pool.get('hr.contract').browse(self._cr, SUPERUSER_ID,contract_ids)
            # for contract in contract_ids:
            for contract in self.employee_id.contract_ids:
                cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)
                cont_end_date = False
                if not contract.date_end:
                    if cont_start_date <= temp_date:
                        day_hours += self.get_hours(weekday, contract.working_hours.attendance_ids)
                else:
                    cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
                    if cont_start_date <= temp_date and cont_end_date >= temp_date:
                        day_hours += self.get_hours(weekday, contract.working_hours.attendance_ids)
            res.update({temp_date:day_hours})
            temp_date += timedelta(days=1)
        plan_hr_obj = self.env['planned.hours']
        dts = res.keys()
        for plan_hrs in self.planned_ids:
            sheet_date = datetime.strptime(plan_hrs.sheet_date, DEFAULT_SERVER_DATE_FORMAT)
            if sheet_date not in dts:
                sheet_date.unlink()

        for dt, hrs in res.iteritems():
            dt_exist = False
            for plan_hrs in self.planned_ids:
                sheet_date = datetime.strptime(plan_hrs.sheet_date, DEFAULT_SERVER_DATE_FORMAT)
                if sheet_date == dt:
                    dt_exist = True
                    if plan_hrs.duration != hrs:
                        plan_hrs.write({'duration': hrs})
            if not dt_exist:
                vals = {
                    'sheet_date': datetime.strftime(dt, DEFAULT_SERVER_DATE_FORMAT),
                    'duration': hrs,
                    'sheet_id': self.id,
                }
                plan_hr_obj.create(vals)

    def get_hours(self, weekday, atten_ids):
        res = 0.0
        for atten in atten_ids:
            if int(atten.dayofweek) == weekday:
                res += atten.hour_to - atten.hour_from
        return res

    @api.depends("timesheet_ids.unit_amount")
    @api.one
    def calc_actual_ot(self):
        if self.state not in ['new', 'draft']:
            # self.actual_ot = self.employee_id.overtime_count
            # newovertime
            self.actual_ot = self.employee_id.employee_overtime_id.emp_overtime_count
            return True
        act_wk_dict = {}
        act_working = 0.0
        for timesheet in self.timesheet_ids:
            tm = act_wk_dict.get(timesheet.date, 0.0) + timesheet.unit_amount
            act_wk_dict.update({timesheet.date: tm})
            act_working += timesheet.unit_amount
        wk_dts = act_wk_dict.keys()
        pln_wk_dict = {}
        pl_working = 0.0
        for pln_hr in self.planned_ids:
            pln_wk_dict.update({pln_hr.sheet_date: pln_hr.duration})
        is_cur_sheet = False
        cur_date = datetime.today()
        date_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)
        if date_from <= cur_date and date_to >= cur_date:
            is_cur_sheet = True
        tot_time = 0.0
        while date_from <= date_to:
            if is_cur_sheet and date_from > cur_date:
                date_from += timedelta(days=1)
                continue
            dt_str = datetime.strftime(date_from, DEFAULT_SERVER_DATE_FORMAT)
            tot_time += act_wk_dict.get(dt_str, 0.0) - pln_wk_dict.get(dt_str, 0.0)
            date_from += timedelta(days=1)
        # print"emp overtime----",self.employee_id.overtime_count
        # print"tot_time--------",tot_time

        # add a logic to add all the overtime hr for the current month
        date_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
        first_date = (date_from + relativedelta(months=-1)).replace(day=1)
        monthly_overtime = 0.0
        while first_date <= date_from:
            timesheet_record = self.search([('date_from','=',first_date),('employee_id','=',self.employee_id.id),('state','in',['new','draft'])],limit=1)
            if timesheet_record:
                # print"timesheet_record.time_diff----",timesheet_record.time_diff
                monthly_overtime += timesheet_record.time_diff
            first_date += timedelta(days=1)
        # print"monthly_overtime-----",monthly_overtime
        # self.actual_ot = self.employee_id.overtime_count + monthly_overtime
        # newovertime
        self.actual_ot = self.employee_id.employee_overtime_id.emp_overtime_count + monthly_overtime
        return True

    total_contract_time = fields.Float(_("Total Planned Hours"), compute="cal_tot_cont_time", multi="cal_tot_cont_time")
    time_diff = fields.Float(_("Time Diffrence"), compute="cal_tot_cont_time", multi="cal_tot_cont_time")
    planned_ids = fields.One2many("planned.hours", "sheet_id", _("Planned Hours"))
    actual_ot = fields.Float(_("Actual Overttime Count"), compute="calc_actual_ot")
    timesheet_ids2 = fields.One2many("hr.analytic.timesheet","sheet_id",string="Timesheet")

    total_planned_hours = fields.Float(_("Planned Hours"), compute="cal_total_hours", multi="total_hours")
    total_timesheet_hours =fields.Float(_("Total Hours"), compute="cal_total_hours", multi="total_hours")
    overtime_hours =fields.Float(_("Overtime Hours"), compute="cal_total_hours", multi="total_hours")



class PlannedHours(models.Model):

    _name = 'planned.hours'

    sheet_date = fields.Date("Date")
    duration = fields.Float("Hours")
    sheet_id = fields.Many2one("hr_timesheet_sheet.sheet", 'Sheet')

class ServiceDescription(models.Model):

    _name = 'service.description'

    name = fields.Char("Service Description")
    # sheet_id = fields.Many2one("hr_timesheet_sheet.sheet", 'Sheet')

