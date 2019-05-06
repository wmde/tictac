from openerp import models, api, fields, _
from openerp.osv import osv
from datetime import datetime

class HRHoliday(models.Model):
    _inherit = "hr.holidays"

    holiday_name = fields.Char(string ='Holiday Name')
    state_value = fields.Char(compute='_compute_state_value')

    @api.one
    def _compute_state_value(self):
        self.state_value = dict(self.fields_get(allfields=['state'])['state']['selection'])[self.state]
        return

    def create(self, cr, uid, values, context=None):
        """
        To create holiday list entry calender of leave request

        """
        # following condition is use to give a warning and to calculate no of day leave
        if values.get('date_from') and values.get('date_to'):
            date_from,date_to= values['date_from'],values['date_to']
            # print"Date from----Date to------",len(date_from),len(date_to)
            # print"Date from----Date to------",date_from,date_to

            if len(date_from) == 10:
                date_from = date_from+' 09:00:00'
                values.update({'date_from':date_from})
            if len(date_to) == 10:
                date_to = date_to+' 18:00:00'
                values.update({'date_to':date_to})
            elif len(date_to) == 19:
                date_to = date_to[0:11] + '18:00:00'
                values.update({'date_to':date_to})
            # print"Values-----",values
            if date_from > date_to:
                raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

            # start_date = date_from
            # # stop_date = date_to
            # office_leave_time = self.pool.get('leave.time')
            # office_leave_time_record = office_leave_time.search(cr,uid,[('active','=',True)],limit=1)
            # if office_leave_time_record:
            #     office_leave_time_brw = office_leave_time.browse(cr,uid,office_leave_time_record[0])
            #     if values.get('leave_selection') == 'full_day':
            #         start_time = str(office_leave_time_brw.fullday_start_time)+':00:00'
            #         start_date = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d ')+start_time
            #         # end_time = str(office_leave_time_brw.fullday_end_time)+':00:00'
            #         #stop_date = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d ')+end_time
            #     elif values.get('leave_selection') == 'half_day':
            #         if values.get('half_day_type') == 'morning':
            #             start_time = str(office_leave_time_brw.halfday_morning_start_time)+':00:00'
            #             start_date = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d ')+start_time
            #             # end_time = str(office_leave_time_brw.halfday_morning_end_time)+':00:00'
            #             # stop_date = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d ')+end_time
            #
            #         else:
            #             start_time = str(office_leave_time_brw.halfday_afternoon_start_time)+':00:00'
            #             start_date = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d ')+start_time
            #             # end_time = str(office_leave_time_brw.halfday_afternoon_end_time)+':00:00'
            #             # stop_date = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d ')+end_time
            #
            # values.update({'date_from':start_date})
            # print"START date----end date-----",start_date,stop_date

            # if values.get('leave_selection') and values.get('leave_selection') == 'half_day':
        #         if date_from == date_to:
        #             values.update({'number_of_days_temp':0.5})
        #         else:
        #             print"DATE---From-----",date_from
        #             print"DATE---T-----",date_to
        #             date_from = datetime.datetime.strptime(date_from,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')+' 00:00:00'
        #             date_to = datetime.datetime.strptime(date_to,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')+' 00:00:00'
        #             diff_day = self._get_number_of_days(date_from, date_to)
        #             diff_day = round(math.floor(diff_day))
        #             values.update({'number_of_days_temp':diff_day})

        res = super(HRHoliday, self).create(cr, uid, values, context)

        for hr_holidays_brw in self.browse(cr,uid,res):
            if hr_holidays_brw.state == 'confirm' and hr_holidays_brw.holiday_type == 'employee' and hr_holidays_brw.type == 'remove':
                notes = ''
                if notes:
                    notes = hr_holidays_brw.notes
                meeting_obj = self.pool.get('calendar.event')
                if hr_holidays_brw.holiday_name:
                    name = hr_holidays_brw.holiday_name
                else:
                    name = (hr_holidays_brw.name or _('Leave Request')) +' -To Approve'

                start_date = hr_holidays_brw.date_from
                stop_date = hr_holidays_brw.date_to
                meeting_vals = {
                    'name': name,
                    'categ_ids': hr_holidays_brw.holiday_status_id.categ_id and [(6,0,[hr_holidays_brw.holiday_status_id.categ_id.id])] or [],
                    'duration': hr_holidays_brw.number_of_days_temp * 8,
                    'description': notes,
                    'user_id': hr_holidays_brw.user_id.id,
                    'start':start_date,
                    'stop': stop_date,
                    'allday': False,
                    'state': 'open',            # to block that meeting date in the calendar
                    'class': 'confidential',
                    # 'leave_status':'To Be Approve'
                }
                #Add the partner_id (if exist) as an attendee
                if hr_holidays_brw.user_id and hr_holidays_brw.user_id.partner_id:
                    meeting_vals['partner_ids'] = [(4,hr_holidays_brw.user_id.partner_id.id)]

                ctx_no_email = dict(context or {}, no_email=True)
                meeting_id = meeting_obj.create(cr, uid, meeting_vals, context=ctx_no_email)
                self.write(cr, uid, hr_holidays_brw.id, {'meeting_id': meeting_id})
        return res

    # def holidays_validate(self, cr, uid, ids, context=None):
    #     obj_emp = self.pool.get('hr.employee')
    #     ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
    #     manager = ids2 and ids2[0] or False
    #     self.write(cr, uid, ids, {'state':'validate'})
    #     data_holiday = self.browse(cr, uid, ids)
    #     for record in data_holiday:
    #         if record.double_validation:
    #             self.write(cr, uid, [record.id], {'manager_id2': manager})
    #         else:
    #             self.write(cr, uid, [record.id], {'manager_id': manager})
    #         if record.holiday_type == 'employee' and record.type == 'remove':
    #             meeting_obj = self.pool.get('calendar.event')
    #
    #             # to check for the existing calender events for this type
    #             if record.meeting_id:
    #                 self._create_resource_leave(cr, uid, [record], context=context)
    #                 meeting_obj.write(cr, uid, record.meeting_id, {'name': record.name or _('Leave Request'),})
    #             else:
    #                 meeting_vals = {
    #                     'name': record.name or _('Leave Request'),
    #                     'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
    #                     'duration': record.number_of_days_temp * 8,
    #                     'description': record.notes,
    #                     'user_id': record.user_id.id,
    #                     'start': record.date_from,
    #                     'stop': record.date_to,
    #                     'allday': False,
    #                     'state': 'open',            # to block that meeting date in the calendar
    #                     'class': 'confidential'
    #                 }
    #                 #Add the partner_id (if exist) as an attendee
    #                 if record.user_id and record.user_id.partner_id:
    #                     meeting_vals['partner_ids'] = [(4,record.user_id.partner_id.id)]
    #
    #                 ctx_no_email = dict(context or {}, no_email=True)
    #                 meeting_id = meeting_obj.create(cr, uid, meeting_vals, context=ctx_no_email)
    #                 self._create_resource_leave(cr, uid, [record], context=context)
    #                 self.write(cr, uid, ids, {'meeting_id': meeting_id})
    #         elif record.holiday_type == 'category':
    #             emp_ids = obj_emp.search(cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
    #             leave_ids = []
    #             batch_context = dict(context, mail_notify_force_send=False)
    #             for emp in obj_emp.browse(cr, uid, emp_ids, context=context):
    #                 vals = {
    #                     'name': record.name,
    #                     'type': record.type,
    #                     'holiday_type': 'employee',
    #                     'holiday_status_id': record.holiday_status_id.id,
    #                     'date_from': record.date_from,
    #                     'date_to': record.date_to,
    #                     'notes': record.notes,
    #                     'number_of_days_temp': record.number_of_days_temp,
    #                     'parent_id': record.id,
    #                     'employee_id': emp.id
    #                 }
    #                 leave_ids.append(self.create(cr, uid, vals, context=batch_context))
    #             for leave_id in leave_ids:
    #                 # TODO is it necessary to interleave the calls?
    #                 for sig in ('confirm', 'validate', 'second_validate'):
    #                     self.signal_workflow(cr, uid, [leave_id], sig)
    #     return True