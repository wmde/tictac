# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv.orm import except_orm
import logging
_logger = logging.getLogger(__name__)

class TestHrLeave(TransactionCase):

    def setUp(self):
        super(TestHrLeave, self).setUp()
        cr, uid = self.cr, self.uid

        # Find Employee group
        group_employee_ref = self.registry('ir.model.data').get_object_reference(cr, uid, 'base', 'group_user')
        self.group_employee_id = group_employee_ref and group_employee_ref[1] or False

        # Find Hr User group
        group_hr_user_ref = self.registry('ir.model.data').get_object_reference(cr, uid, 'base', 'group_hr_user')
        self.group_hr_user_ref_id = group_hr_user_ref and group_hr_user_ref[1] or False

        # Find Hr Manager group
        group_hr_manager_ref = self.registry('ir.model.data').get_object_reference(cr, uid, 'base', 'group_hr_manager')
        self.group_hr_manager_ref_id = group_hr_manager_ref and group_hr_manager_ref[1] or False



        self.test_hrmanager_user = self.env['res.users'].create({
            'name': 'Bastien HrManager',
            'login': 'bastien',
            'alias_name': 'bastien',
            'email': 'bastien.hrmanager@example.com',
            'groups_id': [(6, 0, [self.group_employee_id, self.group_hr_manager_ref_id])]
        })

        self.test_hrmanager_employee = self.env['hr.employee'].create({
            'name': 'Hr Manager Test',
            'user_id':self.test_hrmanager_user.id,
        })


        self.test_user = self.env['res.users'].create({
            'name': 'Agrolait Test User',
            'login': 'user',
            'email': 'hro@example.com',
            'signature': '--\nAgr',
            'groups_id': [(6, 0, [self.group_employee_id])]
        })

        self.test_employee = self.env['hr.employee'].create({
            'name': 'Agrolait Test Emp',
            'user_id':self.test_user.id,
            'parent_id':self.test_hrmanager_employee.id,
        })

        working_hours = self.env["resource.calendar"].search([('name','=','45 Hours/Week')])
        struct_id = self.env["hr.payroll.structure"].search([])
        today_date = datetime.now().date()
        test_contract = self.env['hr.contract'].create({
            'name':'test employee contract',
            'employee_id':self.test_employee.id,
            'struct_id':struct_id[0].id,
            'wage':100,
            'date_start':str(today_date.replace(month=01,day=01)),
            'date_end':str(today_date.replace(month=12,day=01)),
            'working_hours':working_hours.id,
            })

    def test_fillup_sick_leave(self):
        """test case to test the sick leave fill up functionality"""
        hr_sick_leave = self.env["hr.sick.leave"]
        hr_analytic_timesheet =self.env['hr.analytic.timesheet']
        today_date = datetime.now().date()
        end_date = today_date+relativedelta(days=1)
        hr_sick_leave_rec = hr_sick_leave.create({
            'start_date':today_date,
            'end_date':end_date,
            })

        hr_sick_leave_rec.with_context(active_ids = [self.test_employee.id]).confirm_sick_time()
        leave_record = hr_analytic_timesheet.search([('date','>=',today_date),('date','<=',end_date),('user_id','<=',self.test_user.id)])
        print"leave_record------",leave_record
        if leave_record:
            _logger.info('-----Sick leave is created.')
        else:
            self.assertEqual(1,2,'Sick leave is not created.')

    def test_create_timesheet(self):
        """test case to test creation of timesheet and planned,fillup hours,closed timesheet"""
        account_journal = self.env['account.analytic.journal'].search([])
        account_analytic = self.env['account.analytic.account'].search([('use_timesheets','=',True),('type','=','contract')])
        timesheet_sheet = self.env['hr_timesheet_sheet.sheet'].create({
            'date_from': str(datetime.today()),
            'date_to': str(datetime.today()),
            'name': 'Agrolait Test',
            'state': 'new',
            'user_id': self.test_user.id,
            'employee_id': self.test_employee.id,
            'timesheet_ids': [(0, 0, {
                'date':  str(datetime.today()),
                'name': 'Develop yaml for hr module(1)',
                'user_id': self.test_user.id,
                'unit_amount': 8.00,
                'journal_id':account_journal[0].id,
                'account_id':account_analytic[0].id,
        })]})

        try:
            timesheet_sheet.action_timesheet_confirm()
        except Exception:
            pass
        print"Planned hour--------",timesheet_sheet.total_contract_time
        print"total_timesheet-11-------",timesheet_sheet.total_timesheet
        print"actual_ot-11-------",timesheet_sheet.actual_ot
        print"time_diff-11-------",timesheet_sheet.time_diff
        self.assertEqual(timesheet_sheet.actual_ot,timesheet_sheet.time_diff,'Total overtime hour need to be equal.')
        try:
            timesheet_sheet.button_confirm()
        except Exception:
            pass
        self.assertEqual(timesheet_sheet.actual_ot,timesheet_sheet.time_diff,'Total overtime hour need to be equal.')

    def test_create_half_day_leave(self):
        """test half day leave test cases"""

        hr_holidays = self.registry('hr.holidays')
        holidays_status_1 = self.env["hr.holidays.status"].create({
            'name': 'NotLimited',
            'limit': True,
        })
        date_from = datetime.today() + relativedelta(days=2)
        date_end = datetime.today() + relativedelta(days=2)

        timesheet_rec = self.env['hr_timesheet_sheet.sheet'].create({
            'date_from': str(date_from),
            'date_to': str(date_end),
            'name': 'Agrolait Test',
            'state': 'new',
            'user_id': self.test_user.id,
            'employee_id': self.test_employee.id,
        })

        holiday_id = hr_holidays.create(self.cr, self.test_hrmanager_user.id,{
            'name': 'Holiday1',
            'employee_id': self.test_employee.id,
            'holiday_status_id': holidays_status_1.id,
            'date_from': str(date_from),
            'date_to': str(date_end),
            'leave_selection':'half_day',
            'half_day_type':'morning',
            'number_of_days_temp':0.5
        })
        holiday_rec = hr_holidays.browse(self.cr, self.test_hrmanager_user.id, holiday_id)
        self.assertEqual(holiday_rec.state, 'confirm', 'hr_holidays: newly created leave request should be in confirm state')
        self.assertEqual(holiday_rec.number_of_days_temp, 0.5, 'hr_holidays: Half day leave request need to shaw day as 0.5')

        hr_holidays.signal_workflow(self.cr, self.test_hrmanager_user.id, [holiday_id], 'validate')
        self.assertEqual(holiday_rec.state, 'validate', 'hr_holidays: validates leave request should be in validate state')

        leave_record = self.env['hr.analytic.timesheet'].search([('date','>=',date_from),('date','<=',date_end),('user_id','<=',self.test_user.id)])
        if leave_record:
            _logger.info('-----Half Day leave is created.')
        else:
            self.assertEqual(1,2,'Half Day leave is not created.')


