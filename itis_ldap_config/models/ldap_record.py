# -*- coding: utf-8 -*-
from openerp import models, api, fields, _
import logging
logger = logging.getLogger(__name__)

class ldap_record(models.Model):
    _name = 'ldap.record'

    emp_name= fields.Char()
    emp_no= fields.Char()
    ldap_uname= fields.Char()
    cur_uname=fields.Char()
    user_configured=fields.Boolean(string="User Configured")

    @api.one
    def configure_ldap_user_subfunction(self,context):
        ldap_record = self.env['ldap.record']
        res_users = self.env['res.users']
        if context and context.get('user_id'):
            res_user_rec = res_users.browse(context.get('user_id'))
            ldap_records_brw = ldap_record.search([('user_configured','=',False),('ldap_uname','=',res_user_rec.login)])
            print"ldap_records_brw------",ldap_records_brw
            self.ldap_data_exchange(ldap_records_brw)


    @api.model
    def configure_ldap_user(self):
        #Add a logic to map and search LDAP user
        logger.info("-----Ldap userconfigure cron---- ")
        ldap_record = self.env['ldap.record']
        ldap_records_brw = ldap_record.search([('user_configured','=',False)])
        self.ldap_data_exchange(ldap_records_brw)


    def ldap_data_exchange(self,ldap_records_brw):
        res_users = self.env['res.users']
        hr_employee = self.env['hr.employee']
        for ldap_record_brw in ldap_records_brw:
            old_user =False
            new_user = res_users.search([('login','=',ldap_record_brw.ldap_uname)],limit=1)
            # old_user = res_users.search([('login','=',ldap_record_brw.cur_uname)],limit=1)
            related_emp =hr_employee.search([('identification_id','=',ldap_record_brw.emp_no)],limit=1)
            if related_emp:
                old_user = related_emp.user_id
            logger.info("---Ldap In the cron------ " )
            logger.info("---Ldap new user--main---- %s" %str(new_user))
            logger.info("---Ldap old user---main--- %s" %str(old_user))

            # print"old_user------",old_user.name
            # print"related_emp------",related_emp.name
            if new_user and old_user and related_emp:
                # logger.info("---Ldap new user------ %s" %new_user.login)
                logger.info("---Ldap old user------ %s" %old_user.login)

                related_emp.write({'user_id':new_user.id}) #new user write to emp

                #new user write to old time sheet
                related_timesheet_records = self.env['hr_timesheet_sheet.sheet'].search([('employee_id','=',related_emp.id),('user_id','=',old_user.id)])
                [i.write({'user_id':new_user.id}) for i in related_timesheet_records]

                #new user write to old analytic timesheet (I use the query here as well as write function)
                related_analytic_timesheet_records = self.env['hr.analytic.timesheet'].search([('user_id','=',old_user.id)])
                # related_analytic_ids = related_analytic_timesheet_records.ids
                # self._cr.execute("update hr_analytic_timesheet set for_ldap_modification=true where id in %s",(tuple(related_analytic_ids),))
                # [i.with_context(for_ldap_records=True).write({'user_id':new_user.id}) for i in related_analytic_timesheet_records]
                for i in related_analytic_timesheet_records:
                    if not i.sheet_id:
                        i.line_id.write({'user_id':new_user.id})
                    else:
                        sheet_id = i.sheet_id
                        i.line_id.write({'user_id':new_user.id})
                        self._cr.execute("update hr_analytic_timesheet set sheet_id=%s where id =%s",(sheet_id.id,i.id))

                #new user write to the old leave requests
                related_leave_requests = self.env['hr.holidays'].search([('user_id','=',old_user.id)]).ids
                if related_leave_requests:
                    self._cr.execute('update hr_holidays set user_id=%s where id in %s',(new_user.id,tuple(related_leave_requests)))
                # print"Leave requests-------",related_leave_requests

                #new user to the old calendar events
                related_calendar_events = self.env['calendar.event'].search([('user_id','=',old_user.id)]).ids
                # self._cr.execute('update calendar_event set user_id=%s where id in %s',(new_user.id,tuple(related_calendar_events)))
                # print"Calendar Events-------",related_calendar_events
                for event_id in related_calendar_events:
                    if event_id:
                        self.env['calendar.event'].browse(event_id).write({'user_id':new_user.id})

                #assign old user partner to new user and delete or deactivate new user partner
                try:
                    new_user_partner = new_user.partner_id
                    new_user.write({'partner_id':old_user.partner_id.id})
                    new_user_partner.unlink()
                    logger.info("-- Related Partner record can not be link-----")
                except:
                    #Todo Error handling
                    pass

                # old user set to inactive
                old_user.write({'active':False})

                #write configuration is done for this ldap record
                ldap_record_brw.write({'user_configured':True})
                logger.info("---Ldap In the cron---successfull--- " )
