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

from openerp import models, api, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta
import csv
import os
import logging
logger = logging.getLogger(__name__)


class AnalyticAccount(models.Model):

    _inherit = "account.analytic.account"

    account_code = fields.Char("Account Code")


class HRAttendance(models.Model):

    _inherit = "hr.attendance"

    timesheet_id = fields.Many2one("hr.analytic.timesheet", "Anlytic Timesheet")

    @api.model
    def create(self, values):
        t_id = self.env.context.get('timesheet_id', False)
        if t_id:
            values.update({
                'timesheet_id': t_id,
            })
        res = super(HRAttendance, self).create(values)
        if 'action' in values and values['action'] == 'sign_out':
            timesheet_obj = self.env['hr.analytic.timesheet']
            sign_in = self.search([('employee_id', '=', values['employee_id']), ('name', '<', res.name), ('action', '=', ('sign_in'))], limit=1, order='name DESC')
            if sign_in and sign_in.timesheet_id:
                timesheet_obj.browse(sign_in.timesheet_id.id).unit_amount = res.worked_hours
        return res


class HRAnalyticTimesheet(models.Model):

    _inherit = "hr.analytic.timesheet"


    service_desc_id = fields.Many2one('service.description',string="Service Desc")
    emp_comment = fields.Char("Comment")
    dept_account_id = fields.Many2one('account.analytic.account',string="Dept. Analytic Account")
    analytic_account_code = fields.Char(related='account_id.account_code',string="Analytic Account")
    dept_account_code = fields.Char(related='dept_account_id.account_code',string='Dept. Analytic Account')

    identification_id = fields.Char(string="Personal-Nr", compute="get_employee_data")

    @api.model
    def open_analytic_timesheet_tree(self):
        """This function is called from IR.ACTION.SERVER, use to open the analytic timesheet tree view wih required filter"""
        filter_user_ids = []
        hr_employee_recs = self.env['hr.employee'].search([('user_id','!=',False),('parent_id','!=',False)])
        if hr_employee_recs: # to check the condition, current user employee is manager of the record present in the hr.analytic.timesheet
            for hr_employee_rec in hr_employee_recs:
                if hr_employee_rec.parent_id.user_id and hr_employee_rec.parent_id.user_id.id == self._uid:
                    filter_user_ids.append(hr_employee_rec.user_id.id)

        domain = "[('user_id', 'in', " + str(filter_user_ids) + ")]"
        tree_view_id = self.env.ref('itis_hr_attendance_extend.view_timehseet_activity_overview_tree_manager').id
        value = {
            'domain': domain,
            'name': 'Timesheet',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.analytic.timesheet',
            'view_id': tree_view_id,
            'type': 'ir.actions.act_window'
        }
        return value

    @api.one
    def get_employee_data(self):
        """Computed function to get the required data from the hr.employee"""
        hr_employee_rec = self.env['hr.employee'].search([('user_id','=',self.user_id.id)],limit=1)
        if hr_employee_rec:
            self.identification_id = hr_employee_rec.identification_id

    @api.model
    def set_cost_center_existing_rec(self):
        """Call from Scheduler, Use to update dept_account_is for old records"""
        # print"---In set_cost_center_existing_rec-----"
        analytic_timesheet_records = self.search([('dept_account_id','=',False),('sheet_id','!=',False)])
        for analytic_timesheet_brw in analytic_timesheet_records:
            employee_id = analytic_timesheet_brw.sheet_id.employee_id
            if employee_id.bereich and employee_id.bereich.account_id:dept_account_id=employee_id.bereich.account_id.id
            elif employee_id.department_id and employee_id.department_id.account_id:dept_account_id=employee_id.department_id.account_id.id
            else:dept_account_id = False

            if dept_account_id:
                self._cr.execute('update hr_analytic_timesheet set dept_account_id=%s where id =%s',(dept_account_id,analytic_timesheet_brw.id))

    @api.model
    # @api.multi
    def get_monthly_timesheet_overview(self):
        """Call from Scheduler, Use to generate monthly timesheet overview report and send it via email"""

        logger.info("---In the get_monthly_timesheet_overview cron--")
        timesheet_overview_export = self.env['timesheet.overview.export']
        today_date = datetime.today().date()
        last_month_date = today_date -  relativedelta(months= 1)
        # print"today_date----last_month_date--",today_date,last_month_date

        analytic_timesheet_records = self.search([('date','<',today_date),('date','>=',last_month_date)],order='account_id')
        if analytic_timesheet_records:
            logger.info("---Records to get %s" %analytic_timesheet_records)
            # call the subfunction to generate the .csv report
            context = timesheet_overview_export.export_csv_subfunction(analytic_timesheet_records,False)
            if context:
                # create attachement record of the related csv file
                ir_attachment = self.env['ir.attachment']
                file_name ='timesheet_overview_'+str(last_month_date)+'_'+str(today_date)+'.csv'
                attachment_data = {
                        'name': file_name,
                        'datas_fname':file_name,
                        'datas':context.get('default_name'),
                        'res_model': 'email.template',
                    }
                ir_attachment_brw = ir_attachment.create(attachment_data)

                #template = self.env.ref('itis_hr_attendance_extend.email_template_monthly_timesheet_overview', False)
                template = False #Added by IT IS to disable email sending.
                if ir_attachment_brw and template:
                    logger.info("---Template found and send a mail")
                    template.write({'attachment_ids': [(6, 0, [ir_attachment_brw.id])]}) # link a attachment to email template
                    template.send_mail(analytic_timesheet_records[0].id)# send a mail with attachment
                    template.write({'attachment_ids': [(3, ir_attachment_brw.id)]})# to unlink the attachment from template after sending a email


    @api.model
    def create(self, values):
        if values.get('sheet_id'):
            dept_account_id = False
            timesheet_brw = self.env['hr_timesheet_sheet.sheet'].browse(values['sheet_id'])
            if timesheet_brw and timesheet_brw.employee_id:
                employee_id = timesheet_brw.employee_id
                if employee_id.bereich and employee_id.bereich.account_id:dept_account_id=employee_id.bereich.account_id.id
                elif employee_id.department_id and employee_id.department_id.account_id:dept_account_id=employee_id.department_id.account_id.id

            if dept_account_id:
                 values.update({'dept_account_id':dept_account_id})

        if not values.get('name'):
            values.update({'name':'/'})
        return super(HRAnalyticTimesheet, self).create(values)

    @api.one
    def update_hours(self, last_sign_in):

        return True
        lst_dt = datetime.strptime(last_sign_in, DEFAULT_SERVER_DATETIME_FORMAT)
        nw_dt = datetime.today()
        scn = (nw_dt - lst_dt).total_seconds()
        for tm in self:
            unit_amount = scn/360
            tm.write({'unit_amount': unit_amount})
        return True

class hr_employee(models.Model):

    _inherit = 'hr.employee'

    @api.model
    def create(self, values):
        res = super(hr_employee, self).create(values)
        # to create holiday for the related employee
        today_date = datetime.today()
        itis_holiday = self.env['itis.holiday'].search([('date','>',today_date)])
        if itis_holiday:
            hr_holidays_status_brw = self.env['hr.holidays.status'].search([('is_holiday','=',True)],limit=1)
            if hr_holidays_status_brw:
                for hr_employee_brw in res:
                    for itis_holiday_brw in itis_holiday:
                        holiday_created = self.env['hr.holidays'].create({'employee_id':hr_employee_brw.id, 'date_from':itis_holiday_brw.date,'date_to':itis_holiday_brw.date,'holiday_name':itis_holiday_brw.name,'holiday_status_id':hr_holidays_status_brw.id})
                        self._cr.execute("update hr_holidays set state = 'validate' where id = %s",(holiday_created.id,))
        return res
