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
from datetime import datetime, timedelta
from calendar import monthrange
from openerp.exceptions import Warning
import pdb


class HRHolidayStatus(models.Model):

    _inherit = "hr.holidays.status"

    is_holiday = fields.Boolean(string='Is holiday Type')
    is_sick_leave_type = fields.Boolean(string='Is Sick Leave Type')

class HRLeaveNextYear(models.Model):

    _name = "hr.leave.nextyear"

    date = fields.Date('Date')
    holiday_id = fields.Many2one("hr.holidays", "Holiday")
    employee_id = fields.Many2one('hr.employee')
    leave_days = fields.Float('Tage')

class HRLeaveJournal(models.Model):

    _name = "hr.leave.journal"
    _order = "year desc"

    name = fields.Char("Begründung")
    employee_id = fields.Many2one('hr.employee')
    year = fields.Integer('Jahr')
    # year_type = fields.Selection([('actual','aktuell'),('last','Restanspruch')])

    #added for the SOW17
    year_type = fields.Selection([('actual','aktuell'),('last','Restanspruch'),('next','next')])

    type = fields.Selection([('calculate','Vertraglich'),('leave','Ausgleich'),('manual','Manuell'),('additional','Zusatzurlaub')])
    leave_type = fields.Selection([('days','Tage'),('hours','Stunden')])
    leave_start = fields.Date('von')
    leave_end = fields.Date('bis')
    leave_days = fields.Float('Tage')
    leave_hours = fields.Float('Stunden')
    description = fields.Char('Begründung')
    contract_id = fields.Many2one('hr.contract')
    last_year_carry_fwd = fields.Boolean('Last Year Carry Fwd Info')
    leave_id = fields.Many2one('hr.holidays')


class HREmployee(models.Model):

    _inherit = "hr.employee"

    leave_days = fields.Float('Urlaubstage', compute="calculate_actual_year_leave_days")
    leave_days_last_year = fields.Float('Resturlaub', compute="calculate_last_year_leave_days")
    additional_leave_days = fields.Float('Zusatzurlaub', compute="calculate_additional_leave_days")
    sum_leaves = fields.Float('Gesamtanspruch', compute="_calculate_sum_leaves")
    sum_journal_entries = fields.Integer('Anzahl Journaleinträge', compute="_calculate_sum_journal_entries")
    leave_journal_ids = fields.One2many('hr.leave.journal','employee_id')

    approved_leaves = fields.Float('abgegoltene Urlaubstage', compute="_calculate_approved_leave_days")

    #added new field for the following year june1st SOW17
    leave_days_ny = fields.Float('Leaves Following Year', compute="calculate_nextyear_leave_days")
    additional_leave_days_ny = fields.Float('Addtional Leaves Following Year', compute="calculate_nextyear_additional_leave_days")
    approved_leaves_ny = fields.Float('Approve Leaves Following Year', compute="_calculate_nextyear_approved_leave_days")
    sum_leaves_ny = fields.Float('Remaining Leaves Following Year', compute="_calculate_nextyear_sum_leaves")

    #added to maintain data for next year so it will be use for dec scheduler
    nextyear_leave_ids = fields.One2many('hr.leave.nextyear','employee_id')
    approved_leaves_till_march_ny = fields.Float('Approve Leaves Till March', compute="_calculate_nextyear_approved_leave_days_march")
    approved_leaves_after_march_ny = fields.Float('Approve Leaves After March', compute="_calculate_nextyear_approved_leave_days_aft_march")

    #added field to display remaining leaves of last year based on journal entries from that year
    last_year_remaining_leaves = fields.Float('Resturlaub Vorjahr (Zum Jahreswechsel)', compute="calculate_last_year_remaining_leaves")


    @api.one
    def _calculate_nextyear_approved_leave_days_march(self):
        leave_days = 0
        next_year = datetime.today().year+1
        period_date_start = datetime.strptime('01-01-'+str(next_year),'%d-%m-%Y').date()
        period_date_end = datetime.strptime('01-04-'+str(next_year),'%d-%m-%Y').date()
        for nextyear_leave in self.nextyear_leave_ids:
            leave_date = datetime.strptime(nextyear_leave.date,DEFAULT_SERVER_DATE_FORMAT).date()
            if leave_date >=period_date_start and  leave_date < period_date_end:
                leave_days +=nextyear_leave.leave_days
        self.approved_leaves_till_march_ny = leave_days

    @api.one
    def _calculate_nextyear_approved_leave_days_aft_march(self):
        leave_days = 0
        next_year = datetime.today().year+1
        period_date_start = datetime.strptime('01-04-'+str(next_year),'%d-%m-%Y').date()
        period_date_end = datetime.strptime('31-12-'+str(next_year),'%d-%m-%Y').date()
        for nextyear_leave in self.nextyear_leave_ids:
            leave_date = datetime.strptime(nextyear_leave.date,DEFAULT_SERVER_DATE_FORMAT).date()
            if leave_date >=period_date_start and  leave_date <= period_date_end:
                leave_days +=nextyear_leave.leave_days
        self.approved_leaves_after_march_ny = leave_days


    #added new functions for the following year june1st SOW17
    @api.one
    def calculate_nextyear_leave_days(self):
        today_date = datetime.today().date()

        # for sow17
        for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            today_date = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date()

        leave_days = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year_type =='next':# condtion to check year type as next

                period_date_start = datetime.strptime('01-06-'+str(leave_id.year-1),'%d-%m-%Y').date()
                period_date_end = datetime.strptime('01-01-'+str(leave_id.year),'%d-%m-%Y').date()
                if today_date >=period_date_start and  today_date < period_date_end:
                # condition to display value from 01-06-2018 to  03-01-2019,
                # when june scheduler run, this value will display again from june to next jan date

                    if leave_id.type == 'calculate' or leave_id.type == 'manual':
                        leave_days += leave_id.leave_days
        self.leave_days_ny = leave_days
        return

    @api.one
    def calculate_nextyear_additional_leave_days(self):
        today_date = datetime.today().date()

        # for sow17
        for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            today_date = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date()

        leave_days = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year_type =='next':
                period_date_start = datetime.strptime('01-06-'+str(leave_id.year-1),'%d-%m-%Y').date()
                period_date_end = datetime.strptime('01-01-'+str(leave_id.year),'%d-%m-%Y').date()
                if today_date >=period_date_start and  today_date < period_date_end:
                # condition to display value from 01-06-2018 to  03-01-2019,
                # when june scheduler run, this value will display again from june to next jan date
                    if leave_id.type == 'additional':
                        leave_days += leave_id.leave_days
        self.additional_leave_days_ny = leave_days

    @api.one
    def _calculate_nextyear_approved_leave_days(self):
        today_date = datetime.today().date()

        # for sow17 testing
        for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            today_date = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date()

        leave_days = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year_type =='next':
                period_date_start = datetime.strptime('01-06-'+str(leave_id.year-1),'%d-%m-%Y').date()
                period_date_end = datetime.strptime('01-01-'+str(leave_id.year),'%d-%m-%Y').date()
                if today_date >=period_date_start and  today_date < period_date_end:
                # condition to display value from 01-06-2018 to  03-01-2019,
                # when june scheduler run, this value will display again from june to next jan date
                    if leave_id.type == 'leave' and leave_id.leave_type == 'days':
                        leave_days += leave_id.leave_days
        self.approved_leaves_ny = leave_days

    @api.one
    def _calculate_nextyear_sum_leaves(self):
        sum_leaves = self.leave_days_ny  + self.additional_leave_days_ny - self.approved_leaves_ny
        self.sum_leaves_ny = sum_leaves
        return
    #----END----#

    @api.one
    def _calculate_sum_leaves(self):
        sum_leaves = self.leave_days + self.leave_days_last_year + self.additional_leave_days - self.approved_leaves
        self.sum_leaves = sum_leaves
        return

    @api.one
    def _calculate_sum_journal_entries(self):
        journal_entry_ids = self.env['hr.leave.journal'].search([('employee_id.id','=',self.id),('year','=',datetime.today().year)])
        self.sum_journal_entries = len(journal_entry_ids)

    @api.one
    def calculate_actual_year_leave_days(self):
        year = datetime.today().year
        # for sow17 testing
        for_sow17 = self.env['res.company'].search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            year = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().year
        leave_days = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year != year or leave_id.year_type != 'actual':
                continue
            else:
                if leave_id.type == 'calculate':
                    leave_days += leave_id.leave_days
                elif leave_id.type == 'manual':
                    leave_days += leave_id.leave_days
        self.leave_days = leave_days
        return

    @api.one
    def calculate_last_year_leave_days(self):
        month = datetime.today().month
        year = datetime.today().year

        # for sow17 testing
        for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            year = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().year
            month = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().month
        if month > 3:
            self.leave_days_last_year = 0
            return

        leave_days = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year != year or leave_id.year_type != 'last' or leave_id.type == 'manual':
                continue
            else:
                if leave_id.type == 'calculate':
                    leave_days += leave_id.leave_days
                elif leave_id.type == 'leave':
                    leave_days -= leave_id.leave_days
        self.leave_days_last_year = leave_days
        return

    @api.one
    def calculate_additional_leave_days(self):
        year = datetime.today().year

        # for sow17 testing
        for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            year = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().year

        leave_days = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year != year or leave_id.year_type != 'actual':
                continue
            else:
                if leave_id.type == 'additional':
                    leave_days += leave_id.leave_days
        self.additional_leave_days = leave_days
        return

    @api.one
    def _calculate_approved_leave_days(self):
        year = datetime.today().year

        # for sow17 testing
        for_sow17 = self.env['res.company'].sudo().search([('for_sow17','=',True)],limit=1)
        if for_sow17:
            year = datetime.strptime(for_sow17.next_year_date,DEFAULT_SERVER_DATE_FORMAT).date().year

        leave_days = 0
        for leave_id in self.leave_journal_ids:
            # if leave_id.year != year or leave_id.year_type != 'actual':#original
            if leave_id.year != year or leave_id.year_type != 'actual' or leave_id.last_year_carry_fwd: #for sow17 testing
                continue
            else:
                if leave_id.type == 'leave' and leave_id.leave_type == 'days':
                    leave_days += leave_id.leave_days
        self.approved_leaves = leave_days
        return

    # Function to calculate remaining leaves for last year for information purposes
    @api.one
    def calculate_last_year_remaining_leaves(self):
        year = datetime.today().year-1
        #print"Last Year: ",year
        leaves_ly = 0
        for leave_id in self.leave_journal_ids:
            if leave_id.year == year and leave_id.year_type == 'actual' and not leave_id.last_year_carry_fwd:
                if leave_id.type in ['calculate', 'manual', 'additional']:
                    leaves_ly += leave_id.leave_days
                elif leave_id.type == 'leave' and leave_id.leave_type == 'days':
                    leaves_ly -= leave_id.leave_days
        #print"leaves_ly =====> ", leaves_ly
        self.last_year_remaining_leaves = leaves_ly
        return


class HRContract(models.Model):

    _inherit = "hr.contract"

    def create(self, cr, uid, values, context=None):
        new_id = super(HRContract, self).create(cr, uid, values, context=context)
        new_rec = self.browse(cr,uid,new_id, context=context)
        contract_ids = self.pool.get('hr.leave.journal').search(cr, uid, [('employee_id','=', new_rec.employee_id.id),('type','=','calculate'), ('year_type','=','actual'),('year','=', datetime.today().year)])
        if len(contract_ids) == 0:
            self.create_leave_journal_entries(cr,uid,new_id,values)
        return new_id

    @api.one
    def create_leave_journal_entries(self,values):
        leave_journal_obj = self.env['hr.leave.journal']
        leave_days = self.calculate_leave_days(values)
        lj_values = {
            'employee_id': self.employee_id.id,
            'year': datetime.today().year,
            'year_type': 'actual',
            'type': 'calculate',
            'leave_type':'days',
            'leave_days': leave_days[0],
            'name': 'Vertragsanpassung' + str(datetime.today().date()),
            'contract_id': self.id
        }
        leave_journal_obj.create(lj_values)
        return

    @api.one
    def calculate_leave_days(self,values=None,cyear=None):
        leave_days = 0
        if not values:
            values={}
        if not cyear:
            cyear =  datetime.today().year
        date_start = self.date_start
        date_end = self.date_end
        base_leaves = self.base_leaves
        if 'date_start' in values:
            date_start = values['date_start']
        if 'date_end' in values:
            date_end = values['date_end']
        if 'base_leaves' in values:
            base_leaves = values['base_leaves']
        if datetime.strptime(date_start.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year < cyear:
            if not date_end:
                leave_days = base_leaves
            elif datetime.strptime(date_end.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year > cyear:
                leave_days = base_leaves
            # elif datetime.strptime(date_end.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime('01-07-'+str(cyear),'%d-%m-%Y'):
            #     leave_days = base_leaves
            else:
                st = datetime.strptime('01-01-'+str(cyear),'%d-%m-%Y')
                leave_days = self.calculate_partial_year(st, datetime.strptime(date_end.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT), base_leaves)[0]
        elif datetime.strptime(date_start.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year == cyear:
            if not self.date_end:
                date_end = datetime.strptime('31-12-'+str(cyear),'%d-%m-%Y')
            else:
                if datetime.strptime(date_end.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year > cyear:
                    date_end = datetime.strptime('31-12-'+str(cyear),'%d-%m-%Y')
                elif datetime.strptime(date_end.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT).year == cyear:
                    date_end = datetime.strptime(date_end.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            # Contract starts on 01.01, duration is full year so no need to call calculate_partial_year
            ds = datetime.strptime(date_start.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT)
            de = date_end
            #print"date_start: ",ds.year,ds.month,ds.day
            #print"date_end: ",de.year,de.month,de.day
            if ds.year == cyear and ds.month == 1 and ds.day == 1 and de.year == cyear and de.month == 12 and de.day == 31:
                leave_days = base_leaves
            else:
                leave_days = self.calculate_partial_year(datetime.strptime(date_start.split(" ")[0], DEFAULT_SERVER_DATE_FORMAT), date_end, base_leaves)[0]
        return leave_days

    @api.one
    def calculate_partial_year(self,date_start,date_end,base_leaves):
        date_start_calc = date_start
        date_end_calc = date_end
        if date_start.day != 1 or date_start.month != 1:
            date_start_calc = date_start + timedelta(days=-1)
        elif date_end.day != 31 or date_end.month != 12:
            date_end_calc = date_end + timedelta(days=1)
        # else:
        #     return base_leaves
        full_month = date_end_calc.month - date_start_calc.month
        if date_end.day != monthrange(date_end.year, date_end.month)[1] and date_start.day != monthrange(date_start.year, date_start.month)[1]:
            if date_end.day <= date_start.day:
                full_month -= 1
        # if full_month >= 6 and date_end.day >= date_start.day:
        #     leave_days = base_leaves
        # else:
        #     leave_days = float_round(full_month * float(base_leaves) / 12, precision_rounding = 1)
        leave_days = float_round(full_month * float(base_leaves) / 12, precision_rounding = 1)
        return leave_days



