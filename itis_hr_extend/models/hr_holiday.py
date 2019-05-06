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
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import osv
import math

class HRHoliday(models.Model):

    _inherit = "hr.holidays"

    is_ot_leave = fields.Boolean(string="Is OT Leave")
    leave_hours = fields.Float(string="Leave Hours", compute='calc_leave_hours')
    ot_hours = fields.Float(string="Overtime Count", compute="calc_ot_count")
    sum_leaves = fields.Float(string="Gesamtanspruch", compute='calc_sum_leaves')
    # for SOW17
    sum_leaves_ny = fields.Float(string="Next Year Remaining Leaves", compute='calc_ny_sum_leaves')
    number_of_days_temp_ny = fields.Float(string="Next Year Days", compute='calc_number_of_days_temp_ny')

    approved_by = fields.Many2one("res.users", string='Approved/Refuse By')
    approved_at = fields.Datetime(string="Approved/Refuse At")
    ljournal_ids = fields.One2many("hr.leave.journal", "leave_id")

    leave_selection = fields.Selection([('full_day','Full Day'),('half_day','Half Day')], string="Leave Selection",default="full_day")
    leave_selection_date_to = fields.Selection([('full_day','Full Day'),('half_day','Half Day')], string="Leave Selection",default="full_day")
    half_day_type = fields.Selection([('morning','Morning'),('afternoon','Afternoon')], string="Half Day Type")
    half_day_type_date_to = fields.Selection([('morning','Morning'),('afternoon','Afternoon')], string="Half Day Type")
    leave_sele_dateto_flag = fields.Boolean(string='Date to Flag')

    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        """
        # date_to has to be greater than date_from
        # if (date_from and date_to) and (date_from > date_to):
        #     raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.111'))

        result = {'value': {}}
        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=8)
            result['value']['date_to'] = str(date_to_with_delta)

        if date_from and date_to:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            from_dt = datetime.strptime(date_from, DATETIME_FORMAT).date()
            to_dt = datetime.strptime(date_to, DATETIME_FORMAT).date()
            if from_dt == to_dt:
                result['value']['leave_sele_dateto_flag'] =True
            else:
                result['value']['leave_sele_dateto_flag'] =False

            date_from = datetime.strptime(date_from,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')+' 09:00:00'
            date_to = datetime.strptime(date_to,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')+' 18:00:00'

        # Compute and update the number of days
            if date_from <= date_to:
                diff_day = self._get_number_of_days(date_from, date_to)
                result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
            else:
                result['value']['number_of_days_temp'] = 0
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        """
        Update the number_of_days.
        """
        # date_to has to be greater than date_from
        # if (date_from and date_to) and (date_from > date_to):
        #     raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        if date_from and date_to:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            from_dt = datetime.strptime(date_from, DATETIME_FORMAT).date()
            to_dt = datetime.strptime(date_to, DATETIME_FORMAT).date()
            if from_dt == to_dt:
                result['value']['leave_sele_dateto_flag'] =True
            else:
                result['value']['leave_sele_dateto_flag'] =False
            date_from = datetime.strptime(date_from,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')+' 09:00:00'
            date_to = datetime.strptime(date_to,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')+' 18:00:00'
            # Compute and update the number of days
            if date_from <= date_to:

                diff_day = self._get_number_of_days(date_from, date_to)
                result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
            else:
                result['value']['number_of_days_temp'] = 0
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def check_holidays(self, cr, uid, ids, context=None):
        return True

    def check_holidays2(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.holiday_type != 'employee' or record.type != 'remove' or not record.employee_id or record.holiday_status_id.limit:
                continue
            if record.is_ot_leave:
                continue
#           if record.sum_leaves < record.number_of_days_temp:
#           for SOW17
            year = datetime.today().year

            #for SOW17 testing
            for_sow17 = self.pool.get('res.company').search(cr, uid,[('for_sow17','=',True)],limit=1)
            if for_sow17:
                for_sow17 = self.pool.get('res.company').browse(cr,uid,for_sow17)
                year = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().year

            next_year = year+1
            date_from_year = datetime.strptime(record.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year
            date_to_year = datetime.strptime(record.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year

            #warning for the same year leave
            if date_from_year != date_to_year:
                raise Warning(_("Please create a leave request for every year."))

            if date_from_year == next_year+1:
                raise Warning(_('You are not allow to apply leave for the year after next'))

            #warning when user didn't have next year contact or next year vacation
            if date_from_year == next_year and record.sum_leaves_ny==0.0:
                raise Warning(_('The number of next year remaining leaves is not sufficient for this leave type.\n'
                                'Please verify also the leaves waiting for validation.'))

            if record.number_of_days_temp_ny==0.0:#for current year warning
                if record.sum_leaves < record.number_of_days_temp:
                    # Raising a warning gives a more user-friendly feedback than the default constraint error
                    raise Warning(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                'Please verify also the leaves waiting for validation.'))
            else:#next year warning
                if record.sum_leaves_ny < record.number_of_days_temp_ny:
                    raise Warning(_('The number of next year remaining leaves is not sufficient for this leave type.\n'
                                'Please verify also the leaves waiting for validation.'))
        return True

    def _check_date(self, cr, uid, ids, context=None):
        for holiday in self.browse(cr, uid, ids, context=context):
            domain = [
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>=', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_status_id','!=','Holiday')
            ]
            nholidays = self.search_count(cr, uid, domain, context=context)
            if nholidays:
                return False
        return True

    _constraints = [
        (_check_date, 'You can not have 2 leaves that overlaps on same day!', ['date_from','date_to'])
    ]

    def write(self, cr, uid, ids, values, context=None):
        if not context: context = {}
        grp_hr_rec = self.pool.get("ir.model.data").xmlid_to_object(cr, SUPERUSER_ID, "base.group_hr_user")
        hr_usr_id = False
        if 'date_from' in values or 'date_to' in values:
            self.check_holidays2(cr,uid,ids,context=context)
        for usr in grp_hr_rec.users:
            hr_usr_id = usr.id
            break
        if not hr_usr_id:
            hr_usr_id = SUPERUSER_ID
        context.update({'hr_uid':uid})
        return super(HRHoliday, self).write(cr, hr_usr_id, ids, values, context=context)

    @api.multi
    @api.onchange("employee_id")
    @api.depends("employee_id")
    def calc_sum_leaves(self):
        for record in self:
            record.sum_leaves = record.employee_id.sum_leaves

    # for SOW17
    @api.multi
    @api.onchange("employee_id")
    @api.depends("employee_id")
    def calc_ny_sum_leaves(self):
        for record in self:
            record.sum_leaves_ny = record.employee_id.sum_leaves_ny
        return {}

    @api.onchange("number_of_days_temp")
    @api.depends("number_of_days_temp")
    def calc_number_of_days_temp_ny(self):
        for record in self:
            res = 0
            if not record.date_from or not record.date_to:
                return {}
            date_from = datetime.strptime(record.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            date_to = datetime.strptime(record.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            today_date = datetime.today().date()

            # for sow17 testing
            for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
            if for_sow17:
                today_date = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date()

            temp_date = date_from
            while temp_date <= date_to:
                holiday =  None
                holiday = self.env['itis.holiday'].search([('date', '=', temp_date)])
                if holiday:
                    temp_date += timedelta(days=1)
                    continue
                if today_date.year == temp_date.year:
                    temp_date += timedelta(days=1)
                    continue
                weekday = temp_date.weekday()
                for contract in record.employee_id.contract_ids:
                    cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)
                    cont_end_date = False
                    if not contract.date_end:
                        if cont_start_date <= temp_date:
                            if record.get_hours(weekday, contract.working_hours.attendance_ids) > 0.0:
                                if temp_date == date_from and record.leave_selection =='half_day':
                                    res += 0.5
                                    break
                                if temp_date == date_to and record.leave_selection_date_to =='half_day':
                                    res += 0.5
                                    break
                                res += 1
                    else:
                        cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
    #                     cont_end_date += timedelta(days=1)
                        if cont_start_date <= temp_date and cont_end_date >= temp_date:
                            if record.get_hours(weekday, contract.working_hours.attendance_ids) > 0.0:
                                if temp_date == date_from and record.leave_selection =='half_day':
                                    res += 0.5
                                    break
                                if temp_date == date_to and record.leave_selection_date_to =='half_day':
                                    res += 0.5
                                    break
                                res += 1
                temp_date += timedelta(days=1)
            record.number_of_days_temp_ny = res

    #END

    @api.multi
    @api.onchange("employee_id")
    @api.depends("employee_id")
    def calc_ot_count(self):
        for record in self:
        # self.ot_hours = self.employee_id.overtime_count
            record.ot_hours = record.employee_id.employee_overtime_id.emp_overtime_count
        return {}

    @api.multi
    def holidays_refuse(self):
        if self.env.user.id != self.employee_id.parent_id.user_id.id:
            raise Warning(_('Only the Manager of this employee can approve this leave request.'))
        if self.is_ot_leave:
            if self.state in ['validate', 'validate1']:
                new_ot = self.ot_hours + self.leave_hours
                # self.employee_id.sudo().write({'overtime_count': new_ot})
                self.employee_id.sudo().employee_overtime_id.write({'emp_overtime_count': new_ot})
        self.write({"approved_by": self.env.user.id, 'approved_at': datetime.strftime(datetime.today(), DEFAULT_SERVER_DATETIME_FORMAT)})
        for leave_journal_entry in self.ljournal_ids:
            leave_journal_entry.unlink()
        nextyear_leave_data = self.env['hr.leave.nextyear'].search([('holiday_id','=',self.id),('employee_id','=',self.employee_id.id)])
        print'nextyear_leave_data------',nextyear_leave_data
        if nextyear_leave_data:
            nextyear_leave_data.unlink()
        return super(HRHoliday, self).holidays_refuse()

    def holidays_validate_old(self, cr, uid, ids, context=None):
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        self.write(cr, uid, ids, {'state':'validate'})
        data_holiday = self.browse(cr, uid, ids)
        for record in data_holiday:
            if record.double_validation:
                self.write(cr, uid, [record.id], {'manager_id2': manager})
            else:
                self.write(cr, uid, [record.id], {'manager_id': manager})
            if record.holiday_type == 'employee' and record.type == 'remove':
                meeting_obj = self.pool.get('calendar.event')

                # to check for the existing calender events for this type
                if record.meeting_id:
                    self._create_resource_leave(cr, uid, [record], context=context)
                    meeting_obj.write(cr, uid, record.meeting_id, {'name': record.name or _('Leave Request'),})
                else:
                    meeting_vals = {
                        'name': record.name or _('Leave Request'),
                        'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
                        'duration': record.number_of_days_temp * 8,
                        'description': record.notes,
                        'user_id': record.user_id.id,
                        'start': record.date_from,
                        'stop': record.date_to,
                        'allday': False,
                        'state': 'open',            # to block that meeting date in the calendar
                        'class': 'confidential'
                    }
                    #Add the partner_id (if exist) as an attendee
                    if record.user_id and record.user_id.partner_id:
                        meeting_vals['partner_ids'] = [(4,record.user_id.partner_id.id)]

                    ctx_no_email = dict(context or {}, no_email=True)
                    meeting_id = meeting_obj.create(cr, uid, meeting_vals, context=ctx_no_email)
                    self._create_resource_leave(cr, uid, [record], context=context)
                    self.write(cr, uid, ids, {'meeting_id': meeting_id})
            elif record.holiday_type == 'category':
                emp_ids = obj_emp.search(cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
                leave_ids = []
                batch_context = dict(context, mail_notify_force_send=False)
                for emp in obj_emp.browse(cr, uid, emp_ids, context=context):
                    vals = {
                        'name': record.name,
                        'type': record.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': record.holiday_status_id.id,
                        'date_from': record.date_from,
                        'date_to': record.date_to,
                        'notes': record.notes,
                        'number_of_days_temp': record.number_of_days_temp,
                        'parent_id': record.id,
                        'employee_id': emp.id
                    }
                    leave_ids.append(self.create(cr, uid, vals, context=batch_context))
                for leave_id in leave_ids:
                    # TODO is it necessary to interleave the calls?
                    for sig in ('confirm', 'validate', 'second_validate'):
                        self.signal_workflow(cr, uid, [leave_id], sig)
        return True
    @api.multi
    def holidays_validate(self):
        for record in self:
            if self.env.user.id != record.employee_id.parent_id.user_id.id:
                raise Warning(_('Only the Manager of this employee can approve this leave request.'))
            if record.is_ot_leave:
                # commented function customer wants to approve leaves to actual ot_count.
                # User can have positive actual ot count at the end of the month, although the ot_count at employee is negative,
                # because it is updated one time a month only.
                # if self.ot_hours < self.leave_hours:
                #     raise Warning(_('The number of overtime count is not sufficient for Overtime leave.'))
                new_ot = record.ot_hours - record.leave_hours
                # self.employee_id.sudo().write({'overtime_count': new_ot})
                record.employee_id.sudo().employee_overtime_id.write({'emp_overtime_count': new_ot})
        self.check_holidays2()
        self.create_leave_journal_entry()
        self.create_nextyear_leave_entry() #new added.to store the leave data for the next year which will be use for main dec scheduler
        self.write({"approved_by": self.env.user.id, 'approved_at': datetime.strftime(datetime.today(), DEFAULT_SERVER_DATETIME_FORMAT)})
        return self.holidays_validate_old()

    def create_nextyear_leave_entry(self):
        """new added.to store the leave data for the next year which will be use for main dec scheduler
        """
        for record in self:
            year = datetime.today().year

             # for sow17 testing
            for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
            if for_sow17:
                year = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().year

            next_year = year+1
            date_from = datetime.strptime(record.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            date_to = datetime.strptime(record.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)

            if date_from.year == next_year:
                date_data_dict = record.get_date_data(date_from,date_to)
                # print"date_data_dict------",date_data_dict
                for date, day_amt in date_data_dict.iteritems():
                    nextyear_leave_vals={'date':date,'leave_days':day_amt,'employee_id':record.employee_id.id,'holiday_id':record.id}
                    self.env['hr.leave.nextyear'].create(nextyear_leave_vals)


    def get_date_data(self,date_from,date_to):
        """Subfunction of the above function(create_nextyear_leave_entry)"""
        today_date = datetime.today().date()
        temp_date = date_from
        date_data_dict={}
        while temp_date <= date_to:
            holiday =  None
            holiday = self.env['itis.holiday'].search([('date', '=', temp_date)])
            if holiday:
                temp_date += timedelta(days=1)
                continue
            if today_date.year == temp_date.year:
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
                                date_data_dict[temp_date] =0.5
                                break
                            if temp_date == date_to and self.leave_selection_date_to =='half_day':
                                date_data_dict[temp_date] =0.5
                                break
                            date_data_dict[temp_date] =1
                else:
                    cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
#                     cont_end_date += timedelta(days=1)
                    if cont_start_date <= temp_date and cont_end_date >= temp_date:
                        if self.get_hours(weekday, contract.working_hours.attendance_ids) > 0.0:
                            if temp_date == date_from and self.leave_selection =='half_day':
                                date_data_dict[temp_date] =0.5
                                break
                            if temp_date == date_to and self.leave_selection_date_to =='half_day':
                                date_data_dict[temp_date] =0.5
                                break
                            date_data_dict[temp_date] =1
            temp_date += timedelta(days=1)
        return date_data_dict


    def check_same_day(self, date_from, date_to):
        return date_from.date() == date_to.date()

    @api.depends("date_from", "date_to", 'is_ot_leave', 'leave_selection', 'leave_selection_date_to')
    def calc_leave_hours(self):
        for record in self:
            if not record.is_ot_leave:
                return True
            if not record.date_from or not record.date_to:
                return True
            date_from = datetime.strptime(record.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            date_to = datetime.strptime(record.date_to, DEFAULT_SERVER_DATETIME_FORMAT)
            same_day = record.check_same_day(date_from, date_to)
            temp_date = date_from
            day_hours = 0.0

            date_from = datetime.strptime(record.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            date_to = datetime.strptime(record.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            temp_date = date_from
            #temp_date += timedelta(days=1)
            while temp_date <= date_to:
                holiday = self.env['itis.holiday'].search([('date', '=', temp_date)])
                if holiday:
                    temp_date += timedelta(days=1)
                    continue
                weekday = temp_date.weekday()
                for contract in record.employee_id.contract_ids:
                    cont_start_date = datetime.strptime(contract.date_start, DEFAULT_SERVER_DATE_FORMAT)
                    cont_end_date = False
                    if not contract.date_end:
                        if cont_start_date <= temp_date:
                            if (temp_date==date_from and record.leave_selection == 'half_day') or (temp_date.date()==date_from.date() and record.leave_selection_date_to == 'half_day'):
                                day_hours += record.get_hours(weekday, contract.working_hours.attendance_ids)/2
                            else:
                                day_hours += record.get_hours(weekday, contract.working_hours.attendance_ids)
                    else:
                        cont_end_date =  datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
                        if cont_start_date <= temp_date and cont_end_date >= temp_date:
                            if (temp_date==date_from and record.leave_selection == 'half_day') or (temp_date.date()==date_from.date() and record.leave_selection_date_to == 'half_day'):
                                day_hours += record.get_hours(weekday, contract.working_hours.attendance_ids)/2
                            else:
                                day_hours += record.get_hours(weekday, contract.working_hours.attendance_ids)

                temp_date += timedelta(days=1)
            # print"day_hours-----",day_hours
            record.leave_hours = day_hours
        return True

    def get_day_hours(self, date_from, atten_ids):
        weekday = date_from.weekday()
        res = self.get_hours(weekday, atten_ids)
        return res

    def get_hours(self, weekday, atten_ids):
        res = 0.0
        for atten in atten_ids:
            if int(atten.dayofweek) == weekday:
                res += atten.hour_to - atten.hour_from
        return res

    @api.onchange("holiday_status_id")
    def onchange_holiday_status_id(self):
        ot_leave_rec = self.env['ir.model.data'].xmlid_to_object('itis_hr_extend.itis_leave_overtime')
        if ot_leave_rec.id == self.holiday_status_id.id:
            self.is_ot_leave = True
        else:
            self.is_ot_leave = False
        return {}


    #for SOW17, Made some changes in existing function
    def create_leave_journal_entry(self):
        leave_journal_obj = self.env['hr.leave.journal']

        if self.is_ot_leave:
            leave_type = 'hours'
            year = datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year
            if year != datetime.strptime(self.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year:
                raise Warning(_("Please create a leave request for every year."))

            values = {
                'year': year,
                'year_type': 'actual',
                'type': 'leave',
                'leave_type': leave_type,
                'leave_days': self.number_of_days_temp,
                'leave_hours': self.leave_hours,
                'name': self.name,
                'employee_id': self.employee_id.id,
                'leave_start': self.date_from,
                'leave_end': self.date_to,
                'leave_id': self.id
            }
            ljournal_id = leave_journal_obj.create(values)
        else:
            leave_type = 'days'
            year = datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year
            if year != datetime.strptime(self.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year:
                raise Warning(_("Please create a leave request for every year."))

            if self.number_of_days_temp_ny ==0.0: #when leave is apply for the current ongoing year
                yeartype = self.get_year_type()
                print"yeartype------",yeartype
                if len(yeartype)==2 or len(yeartype)==4:
                    leave_days = yeartype[1]
                    values = {
                    'year': year,
                    'year_type': yeartype[0],
                    'type': 'leave',
                    'leave_type': leave_type,
                    'leave_days': leave_days,
                    'name': self.name,
                    'employee_id': self.employee_id.id,
                    'leave_id': self.id
                    }
                    leave_journal_obj.create(values)

                    if len(yeartype)==4:
                        leave_days = yeartype[3]
                        values = {
                        'year': year,
                        'year_type': yeartype[2],
                        'type': 'leave',
                        'leave_type': leave_type,
                        'leave_days': leave_days,
                        'name': self.name,
                        'employee_id': self.employee_id.id,
                        'leave_id': self.id
                        }
                        leave_journal_obj.create(values)
            else:#when there is next year leave in current year
                #------create an next leave for the next year----#
                c_year = datetime.today().date().year
                values = {
                'year': c_year+1,
                'year_type': 'next',
                'type': 'leave',
                'leave_type': leave_type,
                'leave_days': self.number_of_days_temp_ny,
                'name': self.name,
                'employee_id': self.employee_id.id,
                'leave_id': self.id
                }
                leave_journal_obj.create(values)

    def get_year_type(self):
        if datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime('01-04-'+str(datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year),'%d-%m-%Y'):
            return ['actual',self.number_of_days_temp]
        elif datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT) <= datetime.strptime('31-03-'+str(datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year),'%d-%m-%Y'):
            if self.employee_id.leave_days_last_year >= self.number_of_days_temp:
                return ['last',self.number_of_days_temp]
            elif self.employee_id.leave_days_last_year > 0:
                return ['last', self.employee_id.leave_days_last_year,'actual',self.number_of_days_temp-self.employee_id.leave_days_last_year]
            else:
                return ['actual',self.number_of_days_temp]

    # for SOW17 commented this
    # def create_leave_journal_entry(self):
    #         leave_journal_obj = self.env['hr.leave.journal']
    #
    #         if self.is_ot_leave:
    #             leave_type = 'hours'
    #             year = datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year
    #             if year != datetime.strptime(self.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year:
    #                 raise Warning(_("Please create a leave request for every year."))
    #
    #             values = {
    #                 'year': year,
    #                 'year_type': 'actual',
    #                 'type': 'leave',
    #                 'leave_type': leave_type,
    #                 'leave_days': self.number_of_days_temp,
    #                 'leave_hours': self.leave_hours,
    #                 'name': self.name,
    #                 'employee_id': self.employee_id.id,
    #                 'leave_start': self.date_from,
    #                 'leave_end': self.date_to,
    #                 'leave_id': self.id
    #             }
    #             ljournal_id = leave_journal_obj.create(values)
    #         else:
    #             leave_type = 'days'
    #             year = datetime.strptime(self.date_from.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year
    #             if year != datetime.strptime(self.date_to.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year:
    #                 raise Warning(_("Please create a leave request for every year."))
    #             yeartype = self.get_year_type()
    #             if len(yeartype)==2 or len(yeartype)==4:
    #                 leave_days = yeartype[1]
    #                 values = {
    #                 'year': year,
    #                 'year_type': yeartype[0],
    #                 'type': 'leave',
    #                 'leave_type': leave_type,
    #                 'leave_days': leave_days,
    #                 'name': self.name,
    #                 'employee_id': self.employee_id.id,
    #                 'leave_id': self.id
    #                 }
    #                 leave_journal_obj.create(values)
    #
    #                 if len(yeartype)==4:
    #                     leave_days = yeartype[3]
    #                     values = {
    #                     'year': year,
    #                     'year_type': yeartype[2],
    #                     'type': 'leave',
    #                     'leave_type': leave_type,
    #                     'leave_days': leave_days,
    #                     'name': self.name,
    #                     'employee_id': self.employee_id.id,
    #                     'leave_id': self.id
    #                     }
    #                     leave_journal_obj.create(values)
