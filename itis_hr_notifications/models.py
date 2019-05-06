# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta as delta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re


class res_company(models.Model):
     
    _inherit = 'res.company'
     
    training_end_day =  fields.Integer('Training End notification before', help="Training End Notification before months", default=2)
    work_permit = fields.Integer('Work Permit notification before End', help="Work permit Notification before months", default=3)
    term_end = fields.Integer('Term  End notification before', help="Term End Notification before months", default=5)
    savirity = fields.Integer('Savirity notification before', help="Severely handicapped persons", default=2)
    remaining_leaves = fields.Integer('Holiday Season notification before', help="Holiday season Expiration", default=3)

class hr_config_settings(models.TransientModel):
     
    _inherit = 'hr.config.settings'
     
    training_end_day =  fields.Integer('Training End notification before', help="Training End Notification before months", default=2)
    work_permit = fields.Integer('Work Permit notification before End', help="Work permit Notification before months", default=3)
    term_end = fields.Integer('Term  End notification before', help="Term End Notification before months", default=5)
    savirity = fields.Integer('Savirity notification before', help="Severely handicapped persons", default=2)
    remaining_leaves = fields.Integer('Holiday Season notification before', help="Holiday season Expiration", default=3)
    
    
    def get_default_notification(self, cr, uid, fields, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return {
            'training_end_day': user.company_id.training_end_day,
            'work_permit': user.company_id.work_permit,
            'term_end': user.company_id.term_end,
            'savirity': user.company_id.savirity,
            'remaining_leaves': user.company_id.remaining_leaves
        }

    def set_default_notification(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({
            'training_end_day': config.training_end_day,
            'work_permit': config.work_permit,
            'term_end': config.term_end,
            'savirity': config.savirity,
            'remaining_leaves': config.remaining_leaves
        })
    
class hr_notifications(models.Model):
     
    _name='hr.notifications'

    employee_id = fields.Many2one('hr.employee', "Employee")
    user_id = fields.Many2one('res.users', "Employee")
    for_emp = fields.Many2one('hr.employee', "For Employee")
    days = fields.Integer('Days')
    hours = fields.Float("Hours", digits=(5, 2))
    date = fields.Date('Date')
    type = fields.Selection([('training_end','Training End'),
                             ('permit_end','Permit End'),
                             ('term_end','Term End'),
                             ('disability','Disability'),
                             ('leave_balance','Leave Balance'),
                             ('disability','Disability'),
                             ('overtime','Overtime'),
                             ], "Type")
    
    @api.multi
    def send(self):
        template_env = self.env['email.template']
        template = False
        #if self.type == 'training_end':
        #    template = self.env.ref('itis_hr_notifications.email_template_training_end', False)
        #elif self.type == 'permit_end':
        #    template = self.env.ref('itis_hr_notifications.email_template_work_permit_end', False)
        #elif self.type == 'term_end':
        #    template = self.env.ref('itis_hr_notifications.email_template_temp_empl', False)
        #elif self.type == 'disability':
        #    template = self.env.ref('itis_hr_notifications.email_template_emp_disable', False)
        #elif self.type == 'leave_balance':
        #    template = self.env.ref('itis_hr_notifications.email_template_leave_end', False)
        #elif self.type == 'overtime':
        #    template = self.env.ref('itis_hr_notifications.email_template_overtime', False)
        if template:

            template.send_mail(self.id)
            
        
    @api.model
    def create_notification(self, type, data):
        if type == 'training_end':
            mail_dict = self.get_usermail(data.get('emp'),employee=True, manager=True, parent=True)
            for emp in mail_dict.get('employee'):
                vals = {
                    'employee_id': emp.id,
                    'date': data.get('date'),
                    'type': 'training_end',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
            for user in mail_dict.get('users'):
                vals = {
                    'user_id': user.id,
                    'date': data.get('date'),
                    'type': 'training_end',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
        if type == 'permit_end':
            mail_dict = self.get_usermail(data.get('emp'), employee=False, manager=True, parent=True)
            for emp in mail_dict.get('employee'):
                vals = {
                    'employee_id': emp.id,
                    'date': data.get('date'),
                    'type': 'permit_end',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
            for user in mail_dict.get('users'):
                vals = {
                    'user_id': user.id,
                    'date': data.get('date'),
                    'type': 'permit_end',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send() 
        if type == 'term_end':
            mail_dict = self.get_usermail(data.get('emp'), employee=True, manager=True, parent=True)
            for emp in mail_dict.get('employee'):
                vals = {
                    'employee_id': emp.id,
                    'date': data.get('date'),
                    'type': 'term_end',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
            for user in mail_dict.get('users'):
                vals = {
                    'user_id': user.id,
                    'date': data.get('date'),
                    'type': 'term_end',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
        if type == 'disability':
            mail_dict = self.get_usermail(data.get('emp'), employee=True, manager=True, parent=False)
            for emp in mail_dict.get('employee'):
                vals = {
                    'employee_id': emp.id,
                    'date': data.get('date'),
                    'type': 'disability',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
            for user in mail_dict.get('users'):
                vals = {
                    'user_id': user.id,
                    'date': data.get('date'),
                    'type': 'disability',
                    'for_emp':  data.get('emp').id,
                }
                notification = self.create(vals)
                notification.send()
        if type == 'leave_balance':
            mail_dict = self.get_usermail(data.get('emp'), employee=True, manager=False, parent=False)
            for emp in mail_dict.get('employee'):
                vals = {
                    'employee_id': emp.id,
                    'date': data.get('date'),
                    'type': 'leave_balance',
                    'for_emp':  data.get('emp').id,
                    'days': abs(data.get('emp').leave_days + data.get('emp').additional_leave_days - data.get('emp').approved_leaves)
                }
                notification = self.create(vals)
                notification.send()
        if type == 'overtime':
            mail_dict = self.get_usermail(data.get('emp'), employee=True, manager=True, parent=True)
            for emp in mail_dict.get('employee'):
                vals = {
                    'employee_id': emp.id,
                    'date': data.get('date'),
                    'type': 'overtime',
                    'for_emp':  data.get('emp').id,
                    # 'hours': data.get('emp').overtime_count
                    'hours': data.get('emp').employee_overtime_id.emp_overtime_count
                }
                notification = self.create(vals)
                notification.send()
            for user in mail_dict.get('users'):
                vals = {
                    'user_id': user.id,
                    'date': data.get('date'),
                    'type': 'overtime',
                    'for_emp':  data.get('emp').id,
                    # 'hours': data.get('emp').overtime_count
                    'hours': data.get('emp').employee_overtime_id.emp_overtime_count
                }
                notification = self.create(vals)
                notification.send()
    
    @api.model
    def get_usermail(self, emp, employee=False, manager=False, parent=False):
        # print employee, manager, parent
        mail_dict = {'employee': [], 'users': []}
        groups_env = self.env['res.groups']
        
        if employee:
            mail_dict['employee'].append(emp)
        
        if parent:
            if emp and emp.parent_id and emp.parent_id not in mail_dict['employee']:
                mail_dict['employee'].append(emp.parent_id)
        if manager: 
            groups = [self.env.ref('base.group_hr_manager').id]
            for group in groups_env.browse(groups):
                for user in group.users:
                    if user.login and re.match('[^@]+@[^@]+\.[^@]+', user.login):
                        flag = True
                        for emp in mail_dict['employee']:
                            if emp.user_id.id == user.id:
                                flag = False
                        if flag:
                            mail_dict['users'].append(user)
        return mail_dict

        

class hr_contract(models.Model):
    
    _inherit = 'hr.contract'

    @api.model
    def send_notification(self):
        notify_env = self.env['hr.notifications']
        user_rec = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        contract_ids = self.search([])
        for rec in contract_ids:
            today = datetime.now()#.strftime(DF)
            #training_check
            if rec.trial_date_end:
                exp = user_rec.company_id.training_end_day or 1
                date_after_month = today + delta(weeks=exp)
                if date_after_month.strftime(DF) == rec.trial_date_end:
                    data_dict = {"emp":rec.employee_id, 'date': rec.trial_date_end} 
                    notify_env.create_notification('training_end', data_dict)
             
            #work Permit check
            if rec.visa_expire:
                exp = user_rec.company_id.work_permit or 1
                date_after_month = today + delta(weeks=exp)
                if date_after_month.strftime(DF) == rec.visa_expire:
                    data_dict = {"emp":rec.employee_id, 'date': rec.visa_expire}
                    notify_env.create_notification('permit_end', data_dict)
                    
            #end of term
            if rec.date_end:
                exp = user_rec.company_id.term_end or 1
                date_after_month = today + delta(weeks=exp)
                new_contract = self.search([('employee_id', '=', rec.employee_id.id), ('date_start', '>', rec.date_end)])
                if date_after_month.strftime(DF) == rec.date_end and not new_contract:
                    data_dict = {"emp":rec.employee_id, 'date': rec.date_end}
                    notify_env.create_notification('term_end', data_dict)

class hr_employee(models.Model):
    
    _inherit = 'hr.employee'

    @api.model
    def check_disability(self):
        notify_env = self.env['hr.notifications']
        user_rec = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        emp_ids = self.search([('disability_limited_until', '!=', False)])
        exp = user_rec.company_id.savirity or 1
        date_after_month = datetime.now() + delta(weeks=exp)
        for rec in emp_ids:
            if date_after_month.strftime(DF) == rec.disability_limited_until:
                data_dict = {"emp":rec, 'date': rec.disability_limited_until} 
                notify_env.create_notification('disability', data_dict)
        
    @api.model
    def check_leave_bal(self):
        notify_env = self.env['hr.notifications']
        user_rec = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        exp = user_rec.company_id.remaining_leaves or 1
        year_end = datetime(datetime.today().year, 12, 31) 
        emp_ids = self.search([])
        if year_end.strftime(DF) == datetime.now().strftime(DF):
            for rec in emp_ids:
                if rec.leave_days + rec.additional_leave_days - rec.approved_leaves:
                    data_dict = {'emp': rec, 'date':year_end.strftime(DF)}
                    notify_env.create_notification('leave_balance', data_dict)
        
    
    @api.model
    def check_overtime(self):
        emp_ids = self.search([])
        notify_env = self.env['hr.notifications']
        for emp in emp_ids:
            # if emp.overtime_count > 40.0 or emp.overtime_count < -40.0:
            if emp.employee_overtime_id.emp_overtime_count > 39.99 or emp.employee_overtime_id.emp_overtime_count < -39.99:
                data_dict = {'emp': emp}
                notify_env.create_notification('overtime', data_dict)
        return True
    
#     @api.multi
#     def update_overtime_count(self, ot_time, reason):
#         res = super(hr_employee, self).update_overtime_count(ot_time, reason)
#         if self.overtime_count > 0.0:
#             notify_env = self.env['hr.notifications']
#             data_dict = {'emp': self}
#             notify_env.create_notification('overtime', data_dict)
#         return res
            

