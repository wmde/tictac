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


from openerp import models, fields, api, _
from openerp.exceptions import Warning
import csv
from datetime import datetime
import base64
import os

class employee_data_export(models.TransientModel):

    _name = 'employee.data.export'

    name = fields.Binary('Timesheet CSV')
    file_name = fields.Char('File')
    report_selection = fields.Selection([('export_employee','Personalübersicht'),
                                         ('export_workcouncil','BR Übersicht')],
                                        string='Report',default='export_employee', required=True)

    @api.multi
    def export_emp_data_csv(self):
        """
        This function is use to export the employee data records which are preselected.
        """

        if self._context and 'active_model' in self._context and self._context['active_model'] == 'hr.employee':
            context = self._context.copy()
            hr_employee = self.env['hr.employee']
            if self.report_selection =='export_workcouncil':
                hr_employee_records = hr_employee.search([('executive_employee','=',False),('id','in',context['active_ids'])])
            else:
                hr_employee_records = hr_employee.browse(context['active_ids'])
            # print"analytic_timesheet_records----",analytic_timesheet_records
            context = self.export_csv_subfunction(hr_employee_records)

            return {
              'name': _('Exported Employee Data'),
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'employee.data.export',
              'type': 'ir.actions.act_window',
              'context': context,
              'target':'new',
            }

    def get_date_format(self,date):
        if date:
            return datetime.strptime(date,'%Y-%m-%d').strftime('%d.%m.%Y')
        else:
            return ''


    def export_csv_subfunction(self,emp_data_records):
        """
        It is a subfunction for the export csv.
        """

        data_list = []
        if self._context.get('for_work_council') or  self.report_selection =='export_workcouncil':
            csv_header = ['Personalnummer','Vorname','Nachname','Bereich','Team','Stellenbezeichnung','Vertragstyp',
                          'Ersteintrittsdatum','Enddatum befristeter Vertrag','Befristungsgrund','Probezeit Enddatum',
                          'letztes MA Gespraech',]
            csv_name = "Betriebsratsübersicht"

        else:
            csv_header = ['Personalnummer','Vorname','Nachname','Geburtstag','Company','Bereich','Team','Planstellenbezeichnung',
                      'Stellenbezeichnung','Vertragstyp','Ersteintrittsdatum','Enddatum befristeter Vertrag','Befristungsgrund',
                      'Probezeit Enddatum','letztes MA Gespraech','5-Jahresjubilaeum','Arbeitszeit','Urlaub','Schwerbehinderung',
                      'letzte Vertragsaenderung_L&G','Startdatum der letzten Vertragversänderung','Verguetung','Verguetung bei VZ','Verguetung inkl. AG Kosten (25%)','BR Mitglied',
                      'Bemerkungen','Manager']
            csv_name = "Personalübersicht"
        time_csv = datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.csv'
        csv_path = "/tmp/" + time_csv
        for emp_record in emp_data_records:

            if self._context.get('for_work_council') or self.report_selection =='export_workcouncil':
                vals = {
                'Personalnummer': (emp_record.identification_id or '').encode('utf-8'),
                'Nachname': (emp_record.second_name or '').encode('utf-8'),
                'Vorname': (emp_record.surname or '').encode('utf-8'),
                'Bereich': (emp_record.bereich and emp_record.bereich.name or '').encode('utf-8'),
                'Team': (emp_record.department_id and emp_record.department_id.name or '').encode('utf-8'),
                'Stellenbezeichnung': (emp_record.job_id and emp_record.job_id.name or '').encode('utf-8'),
                'Vertragstyp': (emp_record.sudo().contract_type and emp_record.sudo().contract_type.name or '').encode('utf-8'),
                'Ersteintrittsdatum': self.get_date_format(emp_record.initial_date),
                'Enddatum befristeter Vertrag':  self.get_date_format(emp_record.temp_contract_end_date),
                'Befristungsgrund': (emp_record.contract_limitation_reason and  emp_record.contract_limitation_reason.name or '').encode('utf-8'),
                'Probezeit Enddatum': self.get_date_format(emp_record.contract_trial_end_date),
                'letztes MA Gespraech': self.get_date_format(emp_record.last_ma_conversation_date),

                }

            else:
                notes = ''
                if emp_record.contract_notes:
                    notes= emp_record.contract_notes.replace("\n"," / ")
                vals = {
                'Personalnummer': (emp_record.identification_id or '').encode('utf-8'),
                'Nachname': (emp_record.second_name or '').encode('utf-8'),
                'Vorname': (emp_record.surname or '').encode('utf-8'),
                'Geburtstag': self.get_date_format(emp_record.birthday),
                'Company': (emp_record.address_id and emp_record.address_id.sudo().name or '').encode('utf-8'),
                'Bereich': (emp_record.bereich and emp_record.bereich.name or '').encode('utf-8'),
                'Team': (emp_record.department_id and emp_record.department_id.name or '').encode('utf-8'),
                'Planstellenbezeichnung': (emp_record.planned_job_id and emp_record.planned_job_id.name or '').encode('utf-8'),
                'Stellenbezeichnung': (emp_record.job_id and emp_record.job_id.name or '').encode('utf-8'),
                'Vertragstyp': (emp_record.sudo().contract_type and emp_record.sudo().contract_type.name or '').encode('utf-8'),
                'Ersteintrittsdatum':  self.get_date_format(emp_record.initial_date),
                'Enddatum befristeter Vertrag': self.get_date_format(emp_record.temp_contract_end_date),
                'Befristungsgrund': (emp_record.contract_limitation_reason and  emp_record.contract_limitation_reason.name or '').encode('utf-8'),
                'Probezeit Enddatum': self.get_date_format(emp_record.contract_trial_end_date),
                'letztes MA Gespraech': self.get_date_format(emp_record.last_ma_conversation_date),
                '5-Jahresjubilaeum': self.get_date_format(emp_record.five_years),
                'Arbeitszeit': (emp_record.contract_working_hours and  emp_record.contract_working_hours.name or '').encode('utf-8'),
                'Urlaub': emp_record.contract_leaves or '',
                'Schwerbehinderung': ('ja' if emp_record.disability=='yes' else 'nein' or ''),
                # 'letzte Vertragsaenderung_L&G': emp_record.last_contract_changed_wage or '',
                'letzte Vertragsaenderung_L&G': ("%.2f" % emp_record.last_contract_changed_wage).replace('.',',') or '',
                'Startdatum der letzten Vertragversänderung':self.get_date_format(emp_record.last_contract_changed_date),
                'Verguetung': ("%.2f" % emp_record.emp_wage_cal).replace('.',',') or '',
                # 'Verguetung bei VZ':  emp_record.compensation_at_vz or '',
                'Verguetung bei VZ': ("%.2f" % emp_record.compensation_at_vz).replace('.',',') or '',
                # 'Verguetung inkl. AG Kosten (25%)': emp_record.remuneration_incl_ag_costs or '',
                'Verguetung inkl. AG Kosten (25%)': ("%.2f" % emp_record.remuneration_incl_ag_costs).replace('.',',') or '',
                'BR Mitglied': ('ja' if emp_record.br_member=='yes' else 'nein' or '').encode('utf-8'),
                'Bemerkungen': (notes).encode('utf-8'),
                'Manager': (emp_record.parent_id and  emp_record.parent_id.name or '').encode('utf-8'),

                }
            data_list.append(vals)

        with open(csv_path, 'wb') as csvfile:

            w = csv.DictWriter(csvfile, fieldnames=csv_header, delimiter=';',quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(data_list)
        csvfile.close()

        data = ''
        with open(csv_path, 'rb') as csvfile:
            data = csvfile.read()
            data = data.encode('base64')
        csvfile.close()
        context = self._context.copy()
        file_name = datetime.now().strftime('%Y%m%d_%H_%M')+'_'+csv_name+ '.csv'
        context.update({'default_name': data, 'default_file_name':file_name})
        os.remove(csv_path)
        return context
