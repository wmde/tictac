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
from openerp.tools import float_round
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import Warning
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from openerp import http
from openerp.addons.web.controllers import main as parent_controller
from openerp.http import request, serialize_exception as _serialize_exception
import logging
import re
logger = logging.getLogger(__name__)
import pdb
import logging
logger = logging.getLogger(__name__)

number_select = [(x,str('x')) for x in range(1,7)]

class employee_overtime_count(models.Model):

    _name = 'employee.overtime.count'
    _rec_name = "emp_overtime_count"

    emp_overtime_count = fields.Float(string='Overtime Count')
    employee_id = fields.Many2one('hr.employee',string="Employee")

class resource_calendar(models.Model):
    _inherit = 'resource.calendar'

    hourly_basis = fields.Boolean(string="Hourly Basis")

class itis_contract_type(models.Model):

    _name = 'itis.contract.type'

    name = fields.Char(string="Art")

class planned_job(models.Model):

    _name = 'planned.job'

    name = fields.Char(string="Planstellen")

class itis_confession(models.Model):

    _name = 'itis_confession'

    name = fields.Char(string="Bezeichnung")

class leave_time(models.Model):

    _name = 'leave.time'

    active = fields.Boolean(string="Active")
    fullday_start_time = fields.Integer(string="Start Time")
    fullday_end_time = fields.Integer(string="End Time")
    halfday_morning_start_time = fields.Integer(string="Start Time")
    halfday_morning_end_time = fields.Integer(string="End Time")
    halfday_afternoon_start_time = fields.Integer(string="Start Time")
    halfday_afternoon_end_time = fields.Integer(string="End Time")

class itis_employee_children(models.Model):

    _name = 'itis_employee_children'

    name = fields.Char(string="Name")
    birth_date = fields.Date(string="Geburtsdatum")
    parent_id = fields.Many2one('hr.employee',string="Mitarbeiter")

class itis_limitation_reason(models.Model):

    _name = 'itis_limitation_reason'

    name = fields.Char(string="Bezeichnung")


class itis_hr_contact(models.Model):

    _name = 'itis.hr.contact'

    name = fields.Char(index=True, required=1)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char()
    phone = fields.Char()
    fax = fields.Char()
    mobile = fields.Char()

class itis_hr_employee_fte(models.Model):

    _name = 'hr.employee.fte'

    emp_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    fte = fields.Float(string="FTE", digits=(5, 3))

class health_insurance(models.Model):

    _name = 'hr.health.insurance'

    name = fields.Char(string='Name')

class falimy_status(models.Model):

    _name = 'hr.family.status'

    name = fields.Char(string='Status')

class hr_payroll_structure(models.Model):
    _inherit = 'hr.payroll.structure'

    base_on_hours = fields.Boolean(string="Base on Hours")


class itis_hr_employee(models.Model):

    _inherit = 'hr.employee'

    surname = fields.Char(string="Vorname")
    second_name = fields.Char(string="Nachname")
    birth_name = fields.Char(string="Geburtsname")
    taxclass = fields.Selection(selection=[(1,'Steuerklasse 1'),(2,'Steuerklasse 2'),(3,'Steuerklasse 3'),(4,'Steuerklasse 4'),(5,'Steuerklasse 5'),(6,'Steuerklasse 6')], string="Steuerklasse")
    confession = fields.Many2one('itis_confession', string="Konfession")
    health_insurance = fields.Many2one('hr.health.insurance', string="Krankenkasse")
    disability = fields.Selection([('no','nein'),('yes','Ja')], string="Schwerbehinderung")
    disability_limited_until = fields.Date(string="Befristet bis")
    fte = fields.Float(string="FTE", compute="_compute_fte", digits=(5, 3))
    sign_permission = fields.Char(string="Zeichnungsbefugnis")
    active_employee = fields.Boolean(string="Aktiv")
    emergency_contact = fields.Many2one('itis.hr.contact', string='Notfallkontakt')
    emergency_contact2 = fields.Many2one('itis.hr.contact', string='zweiter Notfallkontakt')
    children_ids = fields.One2many('itis_employee_children', 'parent_id', string='Kinder')
    five_years = fields.Date(string="5-Jahres-Jubiläum")
    bereich = fields.Many2one('hr.department', string="Bereich")
    overtime_count = fields.Float(string='Overtime Count')
    fte_ids = fields.One2many('hr.employee.fte', 'emp_id', string="FTEs")
    family_status = fields.Many2one('hr.family.status',string='Familienstand')
    initial_date = fields.Date(string='Ersteintrittsdatum')
    temp_contract_end_date = fields.Date(string='Enddatum befristeter Vertrag',compute="_compute_contract_end_date",multi="contract_end_date")
    wage_info = fields.Text(string='Wage Information')

    br_member = fields.Selection([('no','nein'),('yes','Ja')], string="BR Mitglied")
    position = fields.Char(string="Position")
    planned_job_id = fields.Many2one('planned.job',string='Planstellen')

    employee_meeting_id = fields.Many2one('employee.meeting',compute="_compute_next_emp_meeting",string='Next Meeting')
    employee_instruction_id = fields.Many2one('employee.instruction',compute="_compute_next_emp_instruction_meeting",string='Next Instruction Meeting')

    employee_overtime_id = fields.Many2one('employee.overtime.count',string="Overtime Count New")
    computed_overtime_count = fields.Float(string='Overtime Count',compute="_compute_overtime_count")

    executive_employee = fields.Boolean(string="Executive Employee")
    contract_type = fields.Many2one('hr.contract.type',string="Type", compute="get_active_contract_data", multi="contract_data")
    contract_wage = fields.Float(string="Wage", compute="get_active_contract_data", multi="contract_data")
    contract_leaves = fields.Float(string="Leaves", compute="get_active_contract_data", multi="contract_data")
    contract_notes = fields.Text(string="Notes", compute="get_active_contract_data", multi="contract_data")
    contract_limitation_reason = fields.Many2one('itis_limitation_reason',string="Reason of Limitation", compute="_compute_contract_end_date", multi="contract_end_date")

    contract_working_hours = fields.Many2one('resource.calendar',string="Working Hours", compute="get_active_contract_data", multi="contract_data")
    contract_trial_end_date = fields.Date(string="Trial End Date", compute="get_active_contract_data", multi="contract_data")

    last_ma_conversation_date = fields.Date(string='Last Meeting', compute="_compute_last_emp_meeting")
    # last_ma_conversation= fields.Many2one('employee.meeting',compute="_compute_last_emp_meeting",string='Last Meeting',help='Use to give most recent meeting in the past')
    compensation_at_vz = fields.Float(string="Compensation At VZ", compute="get_active_contract_data", multi="contract_data")
    remuneration_incl_ag_costs = fields.Float(string="Vergütung inkl. AG Kosten (25%)", compute="get_active_contract_data", multi="contract_data")
    last_contract_changed_wage = fields.Float(string="Last Contract Changed Wage", compute="get_active_contract_data", multi="contract_data")
    last_contract_changed_date = fields.Date(string="Last Contract Change Date", compute="get_active_contract_data", multi="contract_data")

    # the below field is use to calculate the employee wage base on the hour as well as normal wage.It called on the scheduler once in the day.
    emp_wage_cal = fields.Float(string="Wage")

    @api.model
    def get_monthly_employee_data(self):
        """Call from Scheduler, Use to generate monthly employee data report and send it via email to work council"""

        logger.info("---In the get_monthly_employee_data cron--")
        today_date = datetime.today().date()
        last_month_date = today_date -  relativedelta(months= 1)
        hr_employee_brw = self.search([('executive_employee','=',False),('active','=',True)],order='id')
        if hr_employee_brw:
            logger.info("---Records to get %s" %hr_employee_brw)
            # call the subfunction to generate the .csv report
            context = self.env['employee.data.export'].with_context(for_work_council=True).export_csv_subfunction(hr_employee_brw)
            if context:
                # create attachement record of the related csv file
                ir_attachment = self.env['ir.attachment']
                file_name ='employee_data_report_'+str(last_month_date)+'_'+str(today_date)+'.csv'
                attachment_data = {
                        'name': file_name,
                        'datas_fname':file_name,
                        'datas':context.get('default_name'),
                        'res_model': 'email.template',
                    }
                ir_attachment_brw = ir_attachment.create(attachment_data)

                #template = self.env.ref('itis_hr_extend.email_template_monthly_employee_data', False)
                template = False #Added by IT IS to disable email sending.
                if ir_attachment_brw and template:
                    logger.info("---Template found and send a mail")
                    template.write({'attachment_ids': [(6, 0, [ir_attachment_brw.id])]}) # link a attachment to email template
                    template.send_mail(hr_employee_brw[0].id)# send a mail with attachment
                    template.write({'attachment_ids': [(3, ir_attachment_brw.id)]})# to unlink the attachment from template after sending a email


    @api.model
    def open_emp_data_tree(self):
        """Add view for the employee data report,called from the server action"""
        filter_employee_ids = []
        today_date = datetime.today().date()
        hr_contract = self.env['hr.contract']
        hr_employee_recs = self.env['hr.employee'].search([('user_id','!=',False),('parent_id','!=',False)])
        if hr_employee_recs:
            for hr_employee_rec in hr_employee_recs:
                active_contract_brw = hr_contract.search([('employee_id','=',hr_employee_rec.id),
                                        ('date_start','<=',today_date),'|',('date_end','>=',today_date),('date_end','=',False)],limit=1)
                if active_contract_brw:
                    filter_employee_ids.append(hr_employee_rec.id)
                    if active_contract_brw.struct_id.base_on_hours:
                        self.calculate_emp_wage(hr_employee_rec,active_contract_brw)
                    else:
                        hr_employee_rec.write({'emp_wage_cal':active_contract_brw.wage})
        # print"filter_employee_ids----",filter_employee_ids

        domain = "[('id', 'in', " + str(filter_employee_ids) + ")]"
        tree_view_id = self.env.ref('itis_hr_extend.hr_emp_data_tree').id
        value = {
            'domain': domain,
            'name': 'Personalübersicht',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.employee',
            'view_id': tree_view_id,
            'type': 'ir.actions.act_window'
        }
        return value

    def calculate_emp_wage(self,hr_employee_rec,active_contract_brw):
        """to calculate the monthly wage base on the hours salary structure
        """
        logger.info("---hr_employee_rec %s" %hr_employee_rec)
        gross_salary = 0.0
        hr_payslip = self.env['hr.payslip']
        year = datetime.today().year
        month = datetime.today().month
        selected_month_range,num_day = monthrange(year,month)
        period_start_date =  datetime.today().date().replace(day=1)
        period_end_date = datetime.today().date().replace(day=num_day)

        contract_date_start = datetime.strptime(active_contract_brw.date_start,'%Y-%m-%d').date()
        if active_contract_brw.date_end:
            contract_date_end = datetime.strptime(active_contract_brw.date_end,'%Y-%m-%d').date()
        else:
            contract_date_end = datetime.today().date()

        if contract_date_start <= period_start_date:
            period_contract_start_date =period_start_date
        else:
            period_contract_start_date =contract_date_start

        if contract_date_end >= period_end_date:
            period_contract_end_date =period_end_date
        else:
            period_contract_end_date =contract_date_end

        logger.info("---period_contract_start_date %s" %period_contract_start_date)
        logger.info("---period_contract_end_date %s" %period_contract_end_date)
        # print"period_contract_start_date---------",period_contract_start_date
        # print"period_contract_end_date---------",period_contract_end_date


        # #To check for the date and values
        if period_contract_start_date > period_contract_end_date:
            period_contract_end_date = period_contract_start_date
            #period_contract_end_date = period_contract_start_date

        period_contract_start_date = str(period_contract_start_date)
        period_contract_end_date = str(period_contract_end_date)

        payslip_values = {'employee_id':active_contract_brw.employee_id.id,'date_from':period_contract_start_date,'date_to':period_contract_end_date,
                          'contract_id':active_contract_brw.id,'struct_id':active_contract_brw.struct_id.id,'journal_id':1 }


        hr_payslip_brw=hr_payslip.sudo().create(payslip_values)

        res = self.pool.get('hr.payslip').onchange_employee_id(self._cr, self._uid, [], period_contract_start_date, period_contract_end_date,
                                   active_contract_brw.employee_id.id, active_contract_brw.id, None)
        if res and res.get('value'):
            value = res.get('value')
            worked_days_line_ids = value.get('worked_days_line_ids')
            for line_rec in worked_days_line_ids:
                line_rec.update({'payslip_id':hr_payslip_brw.id})
                self.env['hr.payslip.worked_days'].create(line_rec)
        hr_payslip_brw.compute_sheet()
        for data in hr_payslip_brw.details_by_salary_rule_category:
            if data.code == "NET":
                gross_salary = data.total
        print"gross_salary-------",gross_salary
        if gross_salary:
            hr_employee_rec.write({'emp_wage_cal':gross_salary})
        hr_payslip_brw.unlink()


    @api.one
    def get_active_contract_data(self):
        """
        Functional fields to get the data from the currently active contract

        """
        today_date = datetime.today().date()
        hr_contract = self.env['hr.contract']
        # active_contract_brw = self.env['hr.contract'].search([('id','=',1)],limit=1)
        active_contract_brw = hr_contract.search([('employee_id','=',self.id),('date_start','<=',today_date),'|',('date_end','>=',today_date),('date_end','=',False)],limit=1)
        if active_contract_brw:
            self.contract_type = active_contract_brw.type_id.id
            self.contract_wage = active_contract_brw.wage
            self.contract_working_hours = active_contract_brw.working_hours
            self.contract_leaves = active_contract_brw.base_leaves
            # self.remuneration_incl_ag_costs = round(active_contract_brw.wage*1.25,2)
            self.remuneration_incl_ag_costs = round(self.emp_wage_cal*1.25,2)
            self.contract_notes = active_contract_brw.notes

            contract_trial_end_date_condition = False
            if not active_contract_brw.trial_date_end:
                contract_trial_end_date_condition = True
            if active_contract_brw.trial_date_end:
                trial_date_end = datetime.strptime(active_contract_brw.trial_date_end, DEFAULT_SERVER_DATE_FORMAT).date()
                if trial_date_end < datetime.today().date():
                    contract_trial_end_date_condition = True
            if contract_trial_end_date_condition:
                #search for the new contract
                new_contracts = hr_contract.search([('employee_id','=',self.id),('date_start','>',active_contract_brw.date_start)],order='date_start')
                for new_contract in new_contracts:
                    if new_contract.trial_date_end:
                        new_trial_date_end = datetime.strptime(new_contract.trial_date_end, DEFAULT_SERVER_DATE_FORMAT).date()
                        if new_trial_date_end >= datetime.today().date():
                            self.contract_trial_end_date = new_contract.trial_date_end
                            break
            else:
                self.contract_trial_end_date = active_contract_brw.trial_date_end

            if self.fte:
                # self.compensation_at_vz = round(active_contract_brw.wage/self.fte,2)
                self.compensation_at_vz = round(self.emp_wage_cal/self.fte,2)

            #Add a condition to search for the old contract and check for the change in the contract wage
            old_contracts = hr_contract.search([('employee_id','=',self.id),('date_start','<',active_contract_brw.date_start)],order='date_start desc')
            # print"old_contract-------",old_contracts,self.id
            middel_contracts =[]
            for old_contract in old_contracts:
                if old_contract.wage!= active_contract_brw.wage:
                    self.last_contract_changed_wage =old_contract.wage
                    # print"middel------",middel_contracts
                    if middel_contracts:
                        for middel_contract in middel_contracts:
                            if middel_contract.wage != old_contract.wage:
                                self.last_contract_changed_date = middel_contract.date_start
                                # break

                    else:
                        self.last_contract_changed_date = active_contract_brw.date_start
                        break
                else:
                    middel_contracts.append(old_contract)



    @api.one
    def _compute_overtime_count(self):
        """computed field, to calculate overtime from the new field"""
        emp_overtime_count = 0.0
        if self.employee_overtime_id:
            emp_overtime_count = self.employee_overtime_id.emp_overtime_count
        self.computed_overtime_count = emp_overtime_count

    @api.model
    def create(self,values):
        employee_overtime_count = self.env['employee.overtime.count']
        res = super(itis_hr_employee, self).create(values)
        for hr_employee in res:
            emp_count_rec = employee_overtime_count.create({'employee_id':hr_employee.id,'emp_overtime_count':0.0})
            hr_employee.write({'employee_overtime_id':emp_count_rec.id})
        return res


    @api.model
    def update_new_overtime_field(self):
        """ Scheduler, Use to update new overtime field. """
        employee_overtime_count = self.env['employee.overtime.count']
        hr_employee = self.env['hr.employee']
        emp_over_count_recs = employee_overtime_count.search([])
        if emp_over_count_recs:emp_over_count_recs.unlink()
        for employee_rec in hr_employee.search([('user_id','!=',False)]):
            emp_count_rec = employee_overtime_count.create({'employee_id':employee_rec.id,'emp_overtime_count':employee_rec.overtime_count})
            employee_rec.write({'employee_overtime_id':emp_count_rec.id})

    @api.one
    def _compute_contract_end_date(self):
        """this function is to calculate the end date of all the contract when there is end date and no gap in contracts"""
        contract_end_date = False
        limitation_reason = False
        if self:
            hr_contract_record = self.env['hr.contract'].search([('employee_id','=',self.id)],order='date_end')
            if hr_contract_record:
                if len(hr_contract_record) ==1:
                    if hr_contract_record[0].date_end:
                        contract_end_date = hr_contract_record[0].date_end
                else:
                    end_date=[]
                    for hr_contract_brw in hr_contract_record:
                        if hr_contract_brw.date_end:
                            # end_date.append(hr_contract_brw.date_end)  ###---new code

                            ###----old code commented
                            next_date_start = datetime.strptime(hr_contract_brw.date_end,DEFAULT_SERVER_DATE_FORMAT).date() + timedelta(days=1)
                            hr_contract_record_new = self.env['hr.contract'].search([('employee_id','=',self.id),('date_start','=',next_date_start)],limit=1)
                            if hr_contract_record_new:
                                if hr_contract_record_new.date_end:
                                    end_date.append(hr_contract_record_new.date_end)
                                else:
                                    end_date=[]
                            else:
                                end_date.append(hr_contract_brw.date_end)
                                break
                            ###---old code is commented END----##
                    if end_date:
                        end_date.sort(reverse=True)
                        if datetime.strptime(end_date[0],DEFAULT_SERVER_DATE_FORMAT).date() >= datetime.today().date():
                            contract_end_date = end_date[0]

        if contract_end_date:
            hr_contract_record_new = self.env['hr.contract'].search([('employee_id','=',self.id),('date_end','=',contract_end_date)],limit=1)
            if hr_contract_record_new:
                limitation_reason = hr_contract_record_new.limitation_reason
        # print"contract_end_date------",contract_end_date
        self.contract_limitation_reason = limitation_reason
        self.temp_contract_end_date = contract_end_date

    @api.onchange("initial_date")
    def onchange_initial_date(self):
        """use to calculate 5 year date for the anniversary when initial date is set"""

        five_year_date =False
        if self.initial_date:
            date_start = datetime.strptime(self.initial_date,DEFAULT_SERVER_DATE_FORMAT).date()
            five_year_date = date_start + relativedelta(years=+5)
        self.five_years = five_year_date

    @api.one
    def _compute_last_emp_meeting(self):
        """
        This computed function is use to find out the mosta recent employee meeting in the past base on the date
        :return:meeting id

        """
        employee_meeting_env ,employee_meeting_brw= self.env['employee.meeting'],False
        employee_meeting_brw = employee_meeting_env.search([('employee_id','=',self.id),('meeting_date', '<=', datetime.today().date())],order='meeting_date desc')
        if employee_meeting_brw:employee_meeting_brw=employee_meeting_brw[0]
        self.last_ma_conversation_date=employee_meeting_brw.meeting_date

    @api.one
    def _compute_next_emp_meeting(self):
        """
        This computed function is use to find out the next employee meeting base on the date
        :return:meeting id
        """

        employee_meeting_env ,employee_meeting_brw= self.env['employee.meeting'],False
        employee_meeting_brw = employee_meeting_env.search([('employee_id','=',self.id),('meeting_date', '>=', datetime.today().date())],order='meeting_date')
        if employee_meeting_brw:employee_meeting_brw=employee_meeting_brw[0]
        self.employee_meeting_id=employee_meeting_brw

    @api.one
    def _compute_next_emp_instruction_meeting(self):
        """
        This computed function is use to find out the next employee instruction meeting base on the date
        :return:instruction meeting id
        """
        employee_instruction_env ,employee_instruction_brw= self.env['employee.instruction'],False
        employee_instruction_brw = employee_instruction_env.search([('employee_id','=',self.id),('meeting_date', '>=', datetime.today().date())],order='meeting_date')
        if employee_instruction_brw:employee_instruction_brw=employee_instruction_brw[0]
        self.employee_instruction_id=employee_instruction_brw

    @api.multi
    def open_ld_change(self):
        return {
            'name': "Last Day Update",
            'res_model': 'ot.change',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'from_ld_change': True}
        }

    @api.multi
    def open_ot_change(self):
        return {
            'name': "Overtime Count Update",
            'res_model': 'ot.change',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'from_ot_change': True}
        }

    @api.multi
    def open_leaved_day_change(self):
        return {
            'name': "Leave Days Update",
            'res_model': 'ld.change',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'current_year':True}
        }

    #for SOW17
    @api.multi
    def open_nextyear_leaved_day_change(self):
        """Add a logic to give ability to change leave day for the next year.
            User can only change it after May month
        """
        if datetime.today().month <6:
            raise Warning(_("You can only change next year leave after May month"))
        return {
            'name': "Next Year Leave Days Update",
            'res_model': 'ld.change',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'next_year':True}
        }

    #for SOW17
    @api.multi
    def open_nextyear_add_day_change(self):
        """Add a logic to give ability to change additional leave day for the next year.
            User can only change it after May month
        """
        if datetime.today().month <6:
            raise Warning(_("You can only change additional leave days for next year after May month"))
        return {
            'name': "Last Day Update",
            'res_model': 'ot.change',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'from_ld_change': True,'next_year':True}
        }

    @api.multi
    def update_overtime_count(self, ot_time, reason):

        # old_ot = self.overtime_count
        # self.write({'overtime_count': ot_time})
        old_ot = self.employee_overtime_id.emp_overtime_count
        self.employee_overtime_id.write({'emp_overtime_count': ot_time})
        leave_journal_obj = self.env['hr.leave.journal']
        # ot_change = ot_time - self.overtime_count
        ot_change = ot_time - self.employee_overtime_id.emp_overtime_count
        values = {
            'employee_id':self.id,
            'year': datetime.today().year,
            'year_type': 'actual',
            'type': 'manual',
            'leave_type':'hours',
            'leave_days': ot_change,
            'name': reason + ' ' + self.name + ' ' + datetime.now().strftime('%d%m%Y %H:%M:%S'),
        }
        leave_journal_obj.create(values)
        msg = _("Overtime has been chagned from <b>%s</b> to <b>%s</b>.<br/>Reason : %s") % \
                    (str(old_ot), str(ot_time), reason)
        self.message_post(body=msg)
        return True

    @api.multi
    def update_leave_day(self, leave_day, reason):
        """Use to update additional leaves"""
        leave_journal_obj = self.env['hr.leave.journal']
        old_additional_day = self.additional_leave_days
        # Added for SOW17
        if self.env.context.get("next_year", False):
            year_type = 'next'
            year = datetime.today().year+1
            old_additional_day = self.additional_leave_days_ny
            leave_days = leave_day - self.additional_leave_days_ny
        else:
            year_type = 'actual'
            year = datetime.today().year
            self.write({'additional_leave_days': leave_day})
            leave_days = leave_day - self.additional_leave_days
        values = {
            'employee_id':self.id,
            'year': year,
            'year_type': year_type,
            'type': 'additional',
            'leave_type':'days',
            'leave_days': leave_days,
            'name': reason + ' ' + self.name + ' ' + datetime.now().strftime('%d%m%Y %H:%M:%S'),
        }
        leave_journal_obj.create(values)

        msg = _("Additional leave has been changed from <b>%s</b> to <b>%s</b>.<br/>Reason : %s") % \
                    (str(old_additional_day), str(leave_day), reason)
        self.message_post(body=msg)
        return True

    def onchange_department_id(self, cr, uid, ids, department_id, context=None):
        value = super(itis_hr_employee,self).onchange_department_id(cr, uid, ids, department_id, context=context)
        value['value']['bereich'] = False
        if department_id:
            department = self.pool.get('hr.department').browse(cr, uid, department_id)
            value['value']['bereich'] = department.parent_id.id
        return value

    @api.one
    def _compute_fte(self):
        contract_obj = self.pool.get('hr.contract')
        contract_ids = contract_obj.search(self._cr, self._uid, [('employee_id', '=', self.id), ('date_start', '<=', datetime.today().date()), '|', ('date_end', '>=', datetime.today().date()),('date_end','=',False)])
        if len(contract_ids) < 1:
            self.fte = 0
        elif len(contract_ids) > 1:
            self.fte = 0
            raise Warning(_("There are 2 contracts assigned to this employee."))
        else:
            work_plan = contract_obj.browse(self._cr, self._uid, contract_ids[0]).working_hours
            weekly_hours = 0.0
            if not work_plan:
                self.fte = 0
            for attendance_id in work_plan.attendance_ids:
                weekly_hours += attendance_id.hour_to - attendance_id.hour_from
            icp_obj = self.env['ir.config_parameter'].sudo()
            fte_base = icp_obj.get_param("fte.base")
            self.fte = float_round(weekly_hours / float(fte_base), precision_digits = 4)

    #add a logic for the 1stjune scheduler for leave calculation request on SOW17
    @api.model
    def june_year_change_calc_days(self):
        """Use for calculation of the leave day for the next year base on the valid contract"""

        leave_journal_obj = self.env['hr.leave.journal']
        contract_obj = self.env['hr.contract']
        error_obj = self.env['itis.leave.days.calc.error']
        logger.info("---------In the Jun calculation vacation cron--------")
        year = datetime.today().year #current year #2018
        next_year = int(year) + 1 #next year #2019

        for employee in self.search([('active','=',True)]):
            # print('employee--name----',employee.name)
            contract_ids_unlimited = contract_obj.search([('employee_id','=',employee.id),('date_start','<=',datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')), ('date_end','=',False)])
            contract_ids_limited = contract_obj.search([('employee_id','=',employee.id),('date_start','<=',datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')), ('date_end', '>=', datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y'))])
            contract_ids_future = contract_obj.search([('employee_id','=',employee.id),('date_start','>',datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')), '|', ('date_end', '>=', datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')),('date_end','=',False)])
            error = False
            #contract_used = False
            #contract_id_used = False
            if len(contract_ids_limited) > 1 or len(contract_ids_unlimited) > 1:
                error = _('Mehr als ein Vertrag zum 01.Januar')
            elif not contract_ids_future:
                if not contract_ids_unlimited and len(contract_ids_limited)==1:
                    leave_days_next_year = contract_ids_limited[0].calculate_leave_days(None,next_year)[0]
                    #contract_used = contract_ids_limited[0]
                elif len(contract_ids_unlimited)==1 and not contract_ids_limited:
                    leave_days_next_year = contract_ids_unlimited[0].calculate_leave_days(None,next_year)[0]
                    #contract_used = contract_ids_unlimited[0]
                elif len(contract_ids_unlimited) > 0 and len(contract_ids_limited) > 0:
                    error = _('Mehr als ein Vertrag zum 01.Januar')
                else:
                    error = _('Kein Vertrag am 01.Januar vorhanden')
            else:
                if len(contract_ids_unlimited) > 0:
                    error = _('Überschneidende Verträge')
                elif not contract_ids_limited and len(contract_ids_future) == 1:
                    leave_days_next_year = contract_ids_future[0].calculate_leave_days(None,next_year)[0]
                    #contract_used = contract_ids_future[0]
                else:
                    answer = self.get_leave_days_from_multiple_contracts(contract_ids_limited.ids or [],contract_ids_future.ids or [],next_year)
                    # print('answer-------',answer)
                    if 'leave_days' in answer:
                        leave_days_next_year = answer['leave_days']
                    elif 'error' in answer:
                        error = answer['error']
                    else:
                        error = _('Fehler in Berechnung')
            #if contract_used:
            #    contract_id_used = contract_used.id
            if not error:
                values_next_year_actual = {
                    'employee_id': employee.id,
                    'year': next_year,
                    'year_type': 'next',
                    'type': 'calculate',
                    'leave_type':'days',
                    'leave_days': leave_days_next_year,
                    'name': _('Berechnung Urlaub zu Jahresbeginn') + str(datetime.today().date()),
                    #'contract_id': contract_id_used,
                }
                leave_journal_obj.create(values_next_year_actual)
            else:
                values_error = {
                    'name': employee.id,
                    'year': next_year,
                    'error': error,
                }
                error_obj.create(values_error)
        pass

    @api.model
    # @api.multi
    def year_change_calc_days(self):
        """
        Imp Note :: This scheduler should run in Dec month.Else remaining leave will have 0 value in it.
        """
        leave_journal_obj = self.env['hr.leave.journal']
        contract_obj = self.env['hr.contract']
        error_obj = self.env['itis.leave.days.calc.error']
        logger.info("---------In the year_change_calc_days cron--------")

        if datetime.today().month == 12 or datetime.today().month == 11:
            year = datetime.today().year
        else:
            year = int(datetime.today().year)-1 #2018
        # year = datetime.today().year
        next_year = int(year) + 1 #2019

        for employee in self.search([('active','=',True)]):
            # print('Employee Name-------',employee.name)
            remaining_leaves = employee.sum_leaves
            addtional_leave = employee.additional_leave_days_ny
            contract_leave = employee.leave_days_ny

            remaining_part_leave = 0.0
            # remaining_part_leave2 = 0.0

            #calculation for the last year leave and total vacation
            if employee.approved_leaves_ny >0.0: #check for the approved leave is there or not.

                #check there is approve leave till march, if it is there reduce it from remaining leave
                if employee.approved_leaves_till_march_ny >0.0:

                    if remaining_leaves > employee.approved_leaves_till_march_ny:
                        remaining_leaves -=employee.approved_leaves_till_march_ny
                    else: #else get a part of it
                        remaining_part_leave = employee.approved_leaves_till_march_ny-remaining_leaves
                        remaining_leaves = 0.0
                    #
                    # if employee.additional_leave_days_ny >0.0: #check for the additional leave
                    #     if remaining_part_leave <=employee.additional_leave_days_ny:
                    #         addtional_leave -=remaining_part_leave
                    #         remaining_part_leave =0.0
                    #     else:
                    #         remaining_part_leave = remaining_part_leave - employee.additional_leave_days_ny
                    #         addtional_leave =0.0
                    #
                    # contract_leave = employee.leave_days_ny - remaining_part_leave

                #check there is approve leave after march, if it is there add it in the remaining_part_leave
                if employee.approved_leaves_after_march_ny >0.0:
                    remaining_part_leave += employee.approved_leaves_after_march_ny
                    # if employee.approved_leaves_after_march_ny <=addtional_leave:
                    #     addtional_leave -=employee.approved_leaves_after_march_ny
                    #     remaining_part_leave2 =0.0
                    # else:
                    #     remaining_part_leave2 = employee.approved_leaves_after_march_ny - addtional_leave
                    #     addtional_leave =0.0
                    #
                    # contract_leave = contract_leave - remaining_part_leave2

            # print"Additional leave-------",addtional_leave
            # print"remaining_leaves-------",remaining_leaves
            # print"contract_leave-------",contract_leave
            # print"Approve leave-------",remaining_part_leave
            # print"sum leave----",contract_leave+remaining_leaves+addtional_leave-remaining_part_leave

            #for leave that is remaining in last year carry forward to next year
            #maintain for current year for info purpose
            #differentiate by last_year_carry_fwd
            values = {
                'employee_id': employee.id,
                'year': year,
                'year_type': 'actual',
                'type': 'leave',
                'leave_type':'days',
                'leave_days': employee.sum_leaves,
                'last_year_carry_fwd':True,
                'name': _('Resturlaub zum Jahreswechsel') + str(datetime.today().date()),
            }
            leave_journal_obj.create(values)

            #for leave that is remaining in last year carry forward to next year
            values_next_year_last = {
                'employee_id': employee.id,
                'year': next_year,
                'year_type': 'last',
                'type': 'calculate',
                'leave_type':'days',
                'leave_days': remaining_leaves,
                'name': _('Umwandlung Resturlaub') + str(datetime.today().date()),
            }
            leave_journal_obj.create(values_next_year_last)

            #for leave base on contract calculated base on june scheduler values
            values_next_year_actual = {
                'employee_id': employee.id,
                'year': next_year,
                'year_type': 'actual',
                'type': 'calculate',
                'leave_type':'days',
                'leave_days': contract_leave,
                'name': _('Berechnung Urlaub zu Jahresbeginn') + str(datetime.today().date()),
                }
            leave_journal_obj.create(values_next_year_actual)

            #to add following year additional leave to current year SOW17
            if addtional_leave > 0.0:
                values_next_year_additional = {
                'employee_id': employee.id,
                'year': next_year,
                'year_type': 'actual',
                'type': 'additional',
                'leave_type':'days',
                'leave_days': addtional_leave,
                'name': _('Berechnung Urlaub zu Jahresbeginn') + str(datetime.today().date()),
                }
                leave_journal_obj.create(values_next_year_additional)

            #for leave approve leave in following year which approve in preceding year carry forward
            values_next_year_last = {
                'employee_id': employee.id,
                'year': next_year,
                'year_type': 'actual',
                'type': 'leave',
                'leave_type':'days',
                'leave_days': remaining_part_leave,
                'name': _('Abgegoltene Urlaubstage') + str(datetime.today().date()),
            }
            leave_journal_obj.create(values_next_year_last)

            #To send an email to employee for the remaining leave
            if remaining_leaves>0.0:
                template = self.env.ref('itis_hr_extend.email_template_remaining_leave_notification', False)
                if template:
                    email_cc_list  = self.get_cc_emails(employee) #to get a cc email address from hr manager,
                    template.with_context(remaining_leaves=remaining_leaves,email_cc = email_cc_list).send_mail(employee.id)

            # Commented as requested on SOW17
            # values_next_year_additional = {
            #     'employee_id': employee.id,
            #     'year': next_year,
            #     'year_type': 'actual',
            #     'type': 'additional',
            #     'leave_type':'days',
            #     'leave_days': employee.additional_leave_days,
            #     'name': _('Berechnung Urlaub zu Jahresbeginn') + str(datetime.today().date()),
            # }
            # leave_journal_obj.create(values_next_year_additional)

            #Below logic is commented as it is transfer to the 1st june scheduler SOW17
            # leave_days_next_year = 0
            # contract_ids_unlimited = contract_obj.search([('employee_id','=',employee.id),('date_start','<=',datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')), ('date_end','=',False)])
            # contract_ids_limited = contract_obj.search([('employee_id','=',employee.id),('date_start','<=',datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')), ('date_end', '>=', datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y'))])
            # contract_ids_future = contract_obj.search([('employee_id','=',employee.id),('date_start','>',datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')), '|', ('date_end', '>=', datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y')),('date_end','=',False)])
            # error = False
            # if len(contract_ids_limited) > 1 or len(contract_ids_unlimited) > 1:
            #     error = _('Mehr als ein Vertrag zum 01.Januar')
            # elif not contract_ids_future:
            #     if not contract_ids_unlimited and len(contract_ids_limited)==1:
            #         leave_days_next_year = contract_ids_limited[0].calculate_leave_days(None,next_year)[0]
            #     elif len(contract_ids_unlimited)==1 and not contract_ids_limited:
            #         leave_days_next_year = contract_ids_unlimited[0].calculate_leave_days(None,next_year)[0]
            #     elif len(contract_ids_unlimited) > 0 and len(contract_ids_limited) > 0:
            #         error = _('Mehr als ein Vertrag zum 01.Januar')
            #     else:
            #         error = _('Kein Vertrag am 01.Januar vorhanden')
            # else:
            #     if len(contract_ids_unlimited) > 0:
            #         error = _('Überschneidende Verträge')
            #     elif not contract_ids_limited and len(contract_ids_future) == 1:
            #         leave_days_next_year = contract_ids_future[0].calculate_leave_days(None,next_year)[0]
            #     else:
            #         answer = self.get_leave_days_from_multiple_contracts(contract_ids_limited.ids or [],contract_ids_future.ids or [],next_year)
            #         if 'leave_days' in answer:
            #             leave_days_next_year = answer['leave_days']
            #         elif 'error' in answer:
            #             error = answer['error']
            #         else:
            #             error = _('Fehler in Berechnung')
            # if not error:
            #     values_next_year_actual = {
            #         'employee_id': employee.id,
            #         'year': next_year,
            #         'year_type': 'actual',
            #         'type': 'calculate',
            #         'leave_type':'days',
            #         'leave_days': leave_days_next_year,
            #         'name': _('Berechnung Urlaub zu Jahresbeginn') + str(datetime.today().date()),
            #     }
            #     leave_journal_obj.create(values_next_year_actual)
            # else:
            #     values_error = {
            #         'name': employee.id,
            #         'year': next_year,
            #         'error': error,
            #     }
            #     error_obj.create(values_error)
        return

    @api.model
    def get_leave_days_from_multiple_contracts(self,contracts1,contracts2,year):
        contract_obj = self.env['hr.contract']
        values = {}
        error = False
        contracts1.extend(contracts2)
        contracts = contract_obj.browse(contracts1)
        if len(contracts) == 1:
            values['start_date'] = contracts[0].start_date
            values['end_date'] = contracts[0].start_date
            leave_days = contracts[0].calculate_leave_days(values,year)[0]
        elif len(contracts) > 1:
            contractvalues = {}
            for contract in contracts:
                workplan_days = 0
                weekdays = {}
                for attendance in contract.working_hours.attendance_ids:
                    if attendance.dayofweek not in weekdays:
                        weekdays[attendance.dayofweek] = True
                workplan_days = len(weekdays)
                contractvalues[contract] = {
                    'date_start' : contract.date_start,
                    'date_end': contract.date_end,
                    'workplan_days': workplan_days,
                    'base_leaves': contract.base_leaves
                }
            contractvalues_sorted = sorted(contractvalues.items(), key=lambda x: x[1]['date_start'])
            date_start = False
            date_end = False
            workplan_days = False
            base_leaves = False
            for contract in contractvalues_sorted:
                if not workplan_days:
                    workplan_days = contract[1]['workplan_days']
                if not base_leaves:
                    base_leaves = contract[1]['base_leaves']
                if not date_start:
                    date_start = contract[1]['date_start']
                if not date_end:
                    date_end = contract[1]['date_end']
                else:
                    if workplan_days == contract[1]['workplan_days']:
                        if base_leaves == contract[1]['base_leaves']:
                            if (datetime.strptime(contract[1]['date_start'], DEFAULT_SERVER_DATE_FORMAT)-datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT)).days ==1:
                                date_end = contract[1]['date_end']
                            else:
                                error = _('Fehler automatische Kalkulation durch keine durchgängigen Arbeitsverträge')
                                break
                        else:
                            error = _('Fehler automatische Kalkulation durch Änderung Urlaubsanspruch')
                            break
                    else:
                        error = _('Fehler automatische Kalkulation durch Änderung Wochenarbeitstage')
                        break
            if not error:
                values = {
                    'date_start':date_start,
                }
                leave_days = contract[0].calculate_leave_days(values,year)[0]
        if error:
            return{'error':error}
        else:
            return {'leave_days':leave_days}

    @api.model
    def leave_request_state_change(self,employee):
        year = datetime.today().year
        leave_to_date = datetime.strptime('31-12-'+str(year),'%d-%m-%Y').date()
        leave_from_date = datetime.strptime('01-01-'+str(year),'%d-%m-%Y').date()
        leaves_ids =self.env['hr.holidays'].search([('employee_id','=',employee.id),('state','in',['draft','confirm'])]).ids
        logger.info("-Employee --------" +str(employee.id))
        # print'employee----',employee.name
        # print'leaves_ids----',leaves_ids
        for leave_id in leaves_ids:
            leave = self.env['hr.holidays'].browse(leave_id)
            from_dt = datetime.strptime(leave.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
            to_dt = datetime.strptime(leave.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
            if leave_to_date >= to_dt and leave_from_date <= from_dt:

                if leave.state=='draft':
                    logger.info("-draft------" +str(leave.id))
                    self._cr.execute("update hr_holidays set state = 'cancel' where id = %s",(leave.id,))
                    template = self.env.ref('itis_hr_extend.email_template_draft_leave_cancel', False)
                    if template:
                        email_cc_list  = self.get_cc_emails(employee) #to get a cc email address from hr manager,
                        template.with_context(date_from=from_dt,date_to =to_dt,email_cc = email_cc_list).send_mail(leave.id)

                if leave.state =='confirm':
                    logger.info("-confirm------" +str(leave.id))
                    try:
                        if leave.employee_id.parent_id:
                            if leave.employee_id.parent_id.user_id:
                                leave.sudo(user=leave.employee_id.parent_id.user_id.id).holidays_validate()
                        else:
                            leave.holidays_validate()
                    except:
                        pass
                    if leave.state =='validate':
                        template = self.env.ref('itis_hr_extend.email_template_toapprove_leave_approve', False)
                        if template:
                            email_cc_list  = self.get_cc_emails(employee) #to get a cc email address from hr manager,
                            template.with_context(date_from=from_dt,date_to =to_dt,email_cc = email_cc_list).send_mail(leave.id)

    @api.model
    def get_cc_emails(self,employee):
        groups = [self.env.ref('base.group_hr_manager').id]
        cc_list = []
        groups_env = self.env['res.groups']
        cc_emails=''
        for group in groups_env.browse(groups):
            for user in group.users:
                if user.login and user.email and re.match('[^@]+@[^@]+\.[^@]+', user.login):

                    if employee and employee.user_id.id != user.id:
                        cc_list.append(user)

        if employee.parent_id and employee.parent_id.user_id and employee.parent_id.user_id.email:
            if employee.parent_id.user_id not in cc_list:
                cc_list.append(employee.parent_id.user_id)
        # print"CC list--------",cc_list
        for i in cc_list:
            cc_emails += i.email+','
        # print('cc_emails-----',cc_emails)
        return cc_emails

    @api.model
    def delete_last_year_leave_days(self):
        """This scheduler is of no use. Not sure why it is added.
        I have added a logic for the make draft leave of this year to cancel and to approve leave with approve.
        Imp Note :: This scheduler should run in Dec month.
        """
        leave_journal_obj = self.env['hr.leave.journal']
        contract_obj = self.env['hr.contract']
        logger.info("---------In the delete last year leave cron--------")
        for employee in self.search([]):
            if not employee.active:
                continue
            to_delete_days = employee.leave_days_last_year - employee.approved_leaves
            if to_delete_days > 0:
                to_delete_days * -1
                values = {
                    'employee_id': employee.id,
                    'year': datetime.today().year,
                    'year_type': 'actual',
                    'type': 'calculate',
                    'leave_type':'days',
                    'leave_days': to_delete_days,
                    'name': _('Verfall Resturlaub') + str(datetime.today().date()),
                }
                leave_journal_obj.create(values)

            #function use to make draft leave of last year rejected and to approve with approve state
            self.leave_request_state_change(employee)

        return


class itis_hr_contract(models.Model):

    _inherit = 'hr.contract'

    itis_contract_type = fields.Many2one('itis.contract.type', string="Art")
    limitation_reason = fields.Many2one('itis_limitation_reason', string="Befristungsgrund")
    base_leaves = fields.Float(string="Urlaubsanspruch", default="20")

class itis_hr_department(models.Model):

    _inherit = 'hr.department'

    planned_fte = fields.Float('Planned FTE')
    account_id = fields.Many2one('account.analytic.account',string="Analytic Account")

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            # if record['parent_id']:
            #     name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res


class itis_leave_days_calc_error(models.Model):
    _name = 'itis.leave.days.calc.error'

    name = fields.Many2one('hr.employee', string='Mitarbeiter')
    year = fields.Integer(string='Jahr')
    error = fields.Char(string='Fehlermeldung')

class MyFilter(parent_controller.DataSet):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'], type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        return_value = self._call_kw(model, method, args, kwargs)
        if model == "hr.employee":
            cr, uid, context = request.cr, request.uid, request.context
            if isinstance(return_value,list):
                for data in return_value:
                    if isinstance(data,dict):
                        if data.get("message_ids",False):
                            res_users_obj = request.registry["res.users"]
                            ir_model_obj = request.registry["ir.model.data"]
                            res_user_data = res_users_obj.browse(cr,uid,[uid],context)
                            xml_list = []
                            group_ids = []
                            for group in res_user_data.groups_id:
                                group_ids.append(group.id)
                            model_ids = ir_model_obj.search(cr,uid,[['model','=','res.groups'],['res_id','in',group_ids]],0,False,False,context)
                            model_data = ir_model_obj.browse(cr,uid,model_ids,context)
                            for value in model_data:
                                xml_list.append(value.name)
                            if "group_hr_manager" in xml_list or "group_hr_payroll_manager" in xml_list or "group_hr_user" in xml_list or uid == 1:
                                continue
                            else:
                                data["message_ids"] = []

        return return_value
