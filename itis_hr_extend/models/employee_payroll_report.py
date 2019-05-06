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
from openerp.exceptions import Warning


class employee_payroll_report(models.TransientModel):

    _name = 'employee.payroll.report'

    @api.one
    def _get_address(self):
        if self.address_home:
            self.address_home_id = unicode(self.address_home.name)
            if self.address_home.street:
                self.address_home_id += ' ' + unicode(self.address_home.street)
            if self.address_home.zip:
                self.address_home_id += ' ' + unicode(self.address_home.zip)
            if self.address_home.city:
                self.address_home_id += ' ' + unicode(self.address_home.city)
        else:
            self.address_home_id = ''
        return

    record_change = fields.Selection([('N','No Change'),('ST','Change Employee'),('V','Change Contract'),('SV','Change Employee Contract')],default='N',string='Change Record')
    sick_days = fields.Float(string='Krankheitstage')
    gross_salary = fields.Float(string='Brattogehalt')
    address_home_id = fields.Char(string="Privatanschrift", compute="_get_address")


    employee_id = fields.Many2one('hr.employee', string="Employee")
    contract_id = fields.Many2one('hr.contract', string='Contract')

    identification_id = fields.Char(related='employee_id.identification_id',string="Personal-Nr")
    name = fields.Char(related='employee_id.second_name',string="Name")
    surname = fields.Char(related='employee_id.surname',string="Vorname")
    birthday = fields.Date(related='employee_id.birthday',string="Geburtsdatum")
    address_home = fields.Many2one(related='employee_id.address_home_id',string="Privatanschrift")
    address_id = fields.Many2one(related='employee_id.address_id',string="Arbeitgeber")
    bank_account_id = fields.Many2one(related='employee_id.bank_account_id',string="Bankverbindung")
    health_insurance = fields.Many2one(related='employee_id.health_insurance',string="Krankenkasse")
    disability = fields.Selection(related='employee_id.disability',string="Schwerbehinderung")
    disability_limited_until = fields.Date(related='employee_id.disability_limited_until',string="Schwerbehinderung Gültigkeit")
    family_status = fields.Many2one(related='employee_id.family_status',string="Familienstand")
    children = fields.Integer(related='employee_id.children',string="Anzahl Kinder")

    contract_name = fields.Char(related='contract_id.name',string="Vertragsreferenz")
    contract_start_date = fields.Date(related='contract_id.date_start',string="Vertragsbeginn")
    contract_end_date = fields.Date(related='contract_id.date_end',string="Vertragsende")
    working_hours = fields.Many2one(related='contract_id.working_hours',string="Arbeitszeit")
    struct_id = fields.Many2one(related='contract_id.struct_id',string="Vergütungsmodell")
    notes = fields.Text(related='contract_id.notes',string="Bemerkung Vertragsinformationen")
    wage = fields.Float(string='Wage')






