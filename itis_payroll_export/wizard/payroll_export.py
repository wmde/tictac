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

class payroll_export(models.TransientModel):

    _name = 'payroll.export'


    name = fields.Binary('Payroll CSV')
    file_name = fields.Char('File')

    @api.model
    def get_sick_days(self, payslip):
        # print "computing days"
#         timesheet_env = self.env['hr.timesheet']
        hr_analytic_env = self.env['hr.analytic.timesheet']
        search_domain = [
            ('date', '>', payslip.date_from),
            ('date', '<=', payslip.date_to),
            ('user_id', '=', payslip.employee_id.user_id.id),
            ('account_id', '=', payslip.company_id.sick_account_id.id)
        ]
        days = 0.0
        timesheet_line_ids = hr_analytic_env.search(search_domain)
        if len(timesheet_line_ids):
            for line in timesheet_line_ids:
                for plan in line.sheet_id.planned_ids:
                    if plan.sheet_date == line.date and plan.duration:
                        days +=line.unit_amount/plan.duration

        return float("{0:.2f}".format(days))

    @api.model
    def get_net(self, payslip):
        amount = 0.0
        for data in payslip.details_by_salary_rule_category:
            if data.code == "NET":
                amount = data.total
        return amount


    @api.multi
    def export_csv(self):
        payslip_env = self.env['hr.payslip']
        if self._context and 'active_model' in self._context and self._context['active_model'] == 'hr.payslip.run':
            slip_ids = self.env['hr.payslip.run'].browse(self._context['active_id']).slip_ids.ids
        else:
            raise Warning(_('Die Aktion bitte immer über den Menüpunkt "Lohnkonten Stapel" aufrufen'))
        payslip_ids = payslip_env.search([('state', '=', 'done'), ('id','in', slip_ids),('credit_note', '=', False)])
        data_list = []
        csv_header = ['Identification', 'Name', 'Krankheitstage', "Gehalt/Lohn", "Remark"]
        time_csv = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.csv'
        csv_path = "/tmp/" + time_csv
        for payslip in payslip_ids:
            emp_name = payslip.employee_id.name
            if payslip.employee_id and payslip.employee_id.surname and payslip.employee_id.second_name:
                emp_name = "%s %s"%(payslip.employee_id.surname or '' , payslip.employee_id.second_name or '')
            vals = {
                "Identification": payslip.employee_id.identification_id or '',
                'Name': emp_name,
                'Krankheitstage': self.get_sick_days(payslip),
                'Gehalt/Lohn': self.get_net(payslip),
                'Remark':payslip.employee_id.wage_info,
            }
            data_list.append(vals)

        # for payslip in payslip_ids:#to write the info with null value
        #     payslip.employee_id.write({'wage_info':''})

        with open(csv_path, 'wb') as csvfile:
            w = csv.DictWriter(csvfile, fieldnames=csv_header, delimiter=';')
            w.writeheader()
            w.writerows(data_list)
        csvfile.close()
        data = ''
        with open(csv_path, 'rb') as csvfile:
            data = csvfile.read()
            data = data.encode('base64')
        csvfile.close()
        context = self._context.copy()
        context.update({'default_name': data, 'default_file_name': 'payroll_export_' + time_csv})
        os.remove(csv_path)
        return {
          'name': _('Exported Payroll'),
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'payroll.export',
          'type': 'ir.actions.act_window',
          'context': context,
          'target':'new',
        }
