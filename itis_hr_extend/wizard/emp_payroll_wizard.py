# -*- coding: utf-8 -*-

from openerp import models, api, fields, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import csv
import os
import base64

def get_years():
    year = []
    for i in range(2016,2040):
        year.append((i,str(i)))
    return year

class create_emp_payroll(models.TransientModel):

    _name = 'create.emp.payroll'

    @api.model
    def _default_date_from(self):
        date = datetime.today().date()
        last_month_date = (date -  relativedelta(months= 1)).replace(day=20)
        return last_month_date

    @api.model
    def _default_date_to(self):
        date = datetime.today().date().replace(day=20)
        return date

    @api.model
    def _default_month(self):
        date = datetime.today().date()
        return date.month

    @api.model
    def _default_year(self):
        date = datetime.today().date()
        return date.year

    month = fields.Selection([(1,'January'),(2,'February'),(3,'March'),(4,'April'),(5,'May'),(6,'June')
        ,(7,'July'),(8,'Augast'),(9,'September'),(10,'October'),(11,'November'),(12,'December')],default =_default_month,string='Month')
    year = fields.Selection(get_years(),default =_default_year,string='Year')
    date_from = fields.Date('Date From',default =_default_date_from)
    date_to = fields.Date('Date To',default =_default_date_to)



    @api.multi
    def generate_employee_report(self):
        emp_payroll_report = self.env['employee.payroll.report']
        record_ids = []


        hr_contract_records = self.env['hr.contract'].search([('employee_id','!=',False)],order='employee_id')
        # hr_contract_records = self.env['hr.contract'].search([('id','=',169)],order='employee_id')
        for hr_contract_brw in hr_contract_records:
            if hr_contract_brw.date_start:
                # print"hr_contract_brw----",hr_contract_brw
                # ----------------to calculate the selected year month combination for the contract
                selected_year_month = str(self.year)+'-'+str(self.month)
                # print"selected_year_month------",selected_year_month

                contract_date_start = datetime.strptime(hr_contract_brw.date_start,'%Y-%m-%d').date()
                if hr_contract_brw.date_end:
                    contract_date_end = datetime.strptime(hr_contract_brw.date_end,'%Y-%m-%d').date()
                else:
                    contract_date_end = datetime.today().date()
                    #Added newly
                    selected_month_range = monthrange(self.year,self.month)
                    selected_month_enddate = datetime.strptime(selected_year_month+'-'+str(selected_month_range[1]),'%Y-%m-%d').date()
                    if contract_date_end < selected_month_enddate:
                        contract_date_end = selected_month_enddate


                contract_date_start_new  = contract_date_start.replace(day=1)
                contract_date_end_new = contract_date_end.replace(day=1)
                # print"contract_date_start_new----",contract_date_start_new
                # print"contract_date_end_new----",contract_date_end_new
                contracted_year_months = []
                while contract_date_start_new <=contract_date_end_new:
                    data = str(contract_date_start_new.year)+'-'+str(contract_date_start_new.month)
                    contracted_year_months.append(data)
                    contract_date_start_new = contract_date_start_new + relativedelta(months= 1)
                # print"contracted_year_months----",contracted_year_months

                # Selected year and month criteria
                # if contract_date_start.year <= self.year and contract_date_start.month <= self.month and contract_date_end.year >= self.year  and contract_date_end.month >= self.month:
                if selected_year_month in contracted_year_months:
                    # print"Active Contract------",hr_contract_brw.name
                    # print"Employee Name ------",hr_contract_brw.employee_id.name

                    # --------------to calculate gross salary
                    gross_salary = 0.0
                    hr_payslip = self.env['hr.payslip']
                    selected_month_range = monthrange(self.year,self.month)

                    period_start_date =  datetime.strptime(selected_year_month+'-01','%Y-%m-%d').date()
                    period_end_date = datetime.strptime(selected_year_month+'-'+str(selected_month_range[1]),'%Y-%m-%d').date()

                    if contract_date_start <= period_start_date:
                        period_contract_start_date =str(period_start_date)
                    else:
                        period_contract_start_date =str(contract_date_start)
                    if contract_date_end >= period_end_date:
                        period_contract_end_date =str(period_end_date)
                    else:
                        period_contract_end_date =str(contract_date_end)

                    #To check for the date and values
                    if period_contract_start_date > period_contract_end_date:
                        period_contract_end_date = period_contract_start_date
                        #period_contract_end_date = period_contract_start_date

                    # print"period_contract_start_date------",period_contract_start_date
                    # print"period_contract_end_date------",period_contract_end_date
                    # print"contract_date_end------",contract_date_end
                    payslip_values = {'employee_id':hr_contract_brw.employee_id.id,'date_from':period_contract_start_date,'date_to':period_contract_end_date,
                                      'contract_id':hr_contract_brw.id,'struct_id':hr_contract_brw.struct_id.id,'journal_id':1 }

                    hr_payslip_brw=hr_payslip.sudo().create(payslip_values)

                    res = self.pool.get('hr.payslip').onchange_employee_id(self._cr, self._uid, [], period_contract_start_date, period_contract_end_date,
                                               hr_contract_brw.employee_id.id, hr_contract_brw.id, None)
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
                    hr_payslip_brw.unlink()


                    # ---------------to calculate sick days
                    sick_days = 0.0
                    selected_date_from = datetime.strptime(self.date_from,'%Y-%m-%d').date()
                    selected_date_to = datetime.strptime(self.date_to,'%Y-%m-%d').date()


                    if contract_date_start<= selected_date_from:
                        sick_leave_start_date = selected_date_from
                    else:
                        sick_leave_start_date = contract_date_start
                    if contract_date_end >= selected_date_to:
                        sick_leave_end_date = selected_date_to
                    else:
                        sick_leave_end_date = contract_date_end

                    while sick_leave_start_date <=sick_leave_end_date:
                        # print"sick_leave_start_date----",sick_leave_start_date

                        hr_analytic_env = self.env['hr.analytic.timesheet']
                        search_domain = [

                            ('date', '=', str(sick_leave_start_date)),
                            ('user_id', '=',hr_contract_brw.employee_id.user_id.id),
                            ('account_id', '=', hr_contract_brw.employee_id.company_id.sick_account_id.id)
                        ]

                        timesheet_line_ids = hr_analytic_env.search(search_domain)
                        # print"timesheet_line_ids--------",timesheet_line_ids
                        if len(timesheet_line_ids):
                            for line in timesheet_line_ids:
                                for plan in line.sheet_id.planned_ids:
                                    if plan.sheet_date == line.date and plan.duration:
                                        sick_days +=line.unit_amount/plan.duration

                        sick_days =  float("{0:.2f}".format(sick_days))

                        # print"sick_days--------",sick_days

                        # sick_day_status = self.env['hr.holidays.status'].search([('is_sick_leave_type','=',True)],limit=1)
                        # if sick_day_status:
                        #     sick_day_leave_records = self.env['hr.holidays'].search([('holiday_status_id','=',sick_day_status.id),('state','=','validate'),
                        #                                 ('employee_id','=',hr_contract_brw.employee_id.id),('date_from','<=',str(sick_leave_start_date)),('date_to','>=',str(sick_leave_start_date))],limit=1)
                        #
                        #     if sick_day_leave_records:
                        #         leave_date_from = datetime.strptime(sick_day_leave_records.date_from,DEFAULT_SERVER_DATETIME_FORMAT).date()
                        #         leave_date_to = datetime.strptime(sick_day_leave_records.date_to,DEFAULT_SERVER_DATETIME_FORMAT).date()
                        #         if leave_date_from == sick_leave_start_date and leave_date_to == sick_leave_start_date:
                        #             sick_days += sick_day_leave_records.number_of_days_temp
                        #         else:
                        #             if leave_date_from == sick_leave_start_date and sick_day_leave_records.leave_selection =='half_day':
                        #                 sick_days +=0.5
                        #             elif leave_date_to == sick_leave_start_date and sick_day_leave_records.leave_selection_date_to =='half_day':
                        #                 sick_days +=0.5
                        #             else:
                        #                 sick_days +=1

                        sick_leave_start_date = sick_leave_start_date+relativedelta(days=1)
                    # print"sick_days------",sick_days


                    # ----------------For coloring base on the last modification date
                    change_record,employee_brw='N',hr_contract_brw.employee_id
                    if self.date_from and self.date_to:
                        if hr_contract_brw.write_date >= self.date_from and hr_contract_brw.write_date <= self.date_to and \
                            employee_brw.write_date >= self.date_from and employee_brw.write_date <= self.date_to:
                            change_record = 'SV'
                        elif self.date_from <= hr_contract_brw.write_date and  self.date_to >= hr_contract_brw.write_date:
                            change_record = 'V'
                        elif self.date_from <= employee_brw.write_date and self.date_to >= employee_brw.write_date:
                            change_record = 'ST'

                    # ----------------To get a wage base on the hourly basis time
                    wage =0.0
                    if hr_contract_brw:
                        wage = hr_contract_brw.wage


                    vals = {'contract_id':hr_contract_brw.id,'employee_id':hr_contract_brw.employee_id.id,
                            'record_change':change_record,'sick_days':sick_days,'gross_salary':gross_salary,'wage':wage}
                    record_ids.append(emp_payroll_report.create(vals).id)

        emp_payroll_report_tree_view = self.env.ref('itis_hr_extend.itis_emp_payroll_report_tree', False)
        return {
            'name': ("Employee Report"),
            'view_mode': 'tree',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'employee.payroll.report',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % record_ids,
            'views': [(emp_payroll_report_tree_view and emp_payroll_report_tree_view.id or False, 'tree')],
            'context': {}
        }



class export_emp_payroll(models.TransientModel):

    _name = 'export.emp.payroll'

    name = fields.Binary('Employee Report CSV')
    file_name = fields.Char('File')

    @api.multi
    def export_csv(self):
        """
        This function is use to export the employee payroll report
        """
        emp_payroll_report = self.env['employee.payroll.report']
        if self._context and 'active_model' in self._context and self._context['active_model'] == 'employee.payroll.report':

            emp_payroll_report_records = emp_payroll_report.browse(self._context['active_ids'])

        data_list = []
        csv_header = ['record_change','Personal-Nr', 'Name', 'Vorname', "Geburtsdatum", "Privatanschrift",'Bankverbindung','Krankenkasse',
                      'Schwerbehinderung','Schwerbehinderung Gültigkeit','Familienstand','Anzahl Kinder',  'Vertragsreferenz','Vertragsbeginn','Vertragsende',
                      'Arbeitszeit','Vergütungsmodell','Bruttogehalt','Wage','Krankheitstage','Bemerkung Vertragsinformationen']
        time_csv = datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv'
        csv_path = "/tmp/" + time_csv

        for emp_report_brw in emp_payroll_report_records:

            bank_info =''
            if emp_report_brw.bank_account_id:
                bank_account_id = emp_report_brw.bank_account_id
                if bank_account_id.state =='iban':
                    bank_info = (bank_account_id.bank_name or ' ') +' '+'IBAN '+(bank_account_id.acc_number or' ')
                else:
                    bank_info = (bank_account_id.bank_name or' ')+' '+(bank_account_id.acc_number or' ')
                if bank_account_id.bank_bic:
                    bank_info = bank_info+' BIC- '+bank_account_id.bank_bic
            #
            record_change = emp_report_brw.record_change
            if record_change =='V':
                record_change = 'VÄ'

            vals = {
            'record_change': record_change,
            'Personal-Nr':(emp_report_brw.identification_id or '').encode('utf-8'),
            "Name": (emp_report_brw.name or '').encode('utf-8'),
            'Vorname': (emp_report_brw.surname or '').encode('utf-8'),
            'Geburtsdatum': emp_report_brw.birthday or '',
            'Privatanschrift': (emp_report_brw.address_home_id or '').encode('utf-8') ,
            'Bankverbindung': bank_info.encode('utf-8'),
            'Krankenkasse': (emp_report_brw.health_insurance and emp_report_brw.health_insurance.name or '').encode('utf-8'),
            'Schwerbehinderung': emp_report_brw.disability or '',
            'Schwerbehinderung Gültigkeit':emp_report_brw.disability_limited_until or '',
            'Familienstand': emp_report_brw.family_status and emp_report_brw.family_status.name or '',
            'Anzahl Kinder': emp_report_brw.children,

            'Vertragsreferenz':(emp_report_brw.contract_name or '').encode('utf-8'),
            'Vertragsbeginn':emp_report_brw.contract_start_date,
            'Vertragsende':emp_report_brw.contract_end_date or '',
            'Arbeitszeit':(emp_report_brw.working_hours and emp_report_brw.working_hours.name or '').encode('utf-8'),
            'Vergütungsmodell':(emp_report_brw.struct_id and emp_report_brw.struct_id.name or '').encode('utf-8'),
            'Bruttogehalt':emp_report_brw.gross_salary,
            'Wage':emp_report_brw.wage,
            'Krankheitstage':emp_report_brw.sick_days,
            'Bemerkung Vertragsinformationen':(emp_report_brw.notes or '').replace('\n',' ').encode('utf-8'),
            }
            data_list.append(vals)

        with open(csv_path, 'wb') as csvfile:

            w = csv.DictWriter(csvfile, fieldnames=csv_header, delimiter=',', quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(data_list)
        csvfile.close()

        data = ''
        with open(csv_path, 'rb') as csvfile:
            data = csvfile.read()
            data = data.encode('base64')
        csvfile.close()
        context = self._context.copy()
        context.update({'default_name': data, 'default_file_name': 'employee_report_export_' + time_csv})
        os.remove(csv_path)

        return {
          'name': _('Exported Employee Report'),
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'export.emp.payroll',
          'type': 'ir.actions.act_window',
          'context': context,
          'target':'new',
        }