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

class timesheet_overview_export(models.TransientModel):

    _name = 'timesheet.overview.export'

    name = fields.Binary('Timesheet CSV')
    file_name = fields.Char('File')

    def export_csv_subfunction(self,analytic_timesheet_records,active_domain):
        data_list = []
        csv_header = ['Personalnummer','Mitarbeitername', "Mitarbeiter Vorname",'Dept. Cost Center','Cost Center', "Dauer(metrisch)",'Description']
        time_csv = datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.csv'
        csv_path = "/tmp/" + time_csv
        for timesheet_overview_brw in analytic_timesheet_records:
            emp_name, emp_first_name,emp_personal_no = '','',''
            if timesheet_overview_brw.sheet_id:
                emp_name = timesheet_overview_brw.sheet_id.employee_id.second_name
                emp_first_name = timesheet_overview_brw.sheet_id.employee_id.surname
                emp_personal_no = timesheet_overview_brw.sheet_id.employee_id.identification_id
            vals = {
            'Personalnummer': (emp_personal_no or '').encode('utf-8'),
            'Dept. Cost Center': (timesheet_overview_brw.dept_account_id.account_code or '').encode('utf-8'),
            'Description': (timesheet_overview_brw.emp_comment or '').encode('utf-8'),
            "Cost Center": (timesheet_overview_brw.account_id.account_code or '').encode('utf-8'),
            'Mitarbeitername': (emp_name or '').encode('utf-8'),
            'Mitarbeiter Vorname': (emp_first_name or '').encode('utf-8'),
            'Dauer(metrisch)': ("%.2f" % timesheet_overview_brw.unit_amount).replace('.',':'),
            # 'Dauer(metrisch)': timesheet_overview_brw.unit_amount,
            }
            data_list.append(vals)

        with open(csv_path, 'wb') as csvfile:
            if active_domain:
                w = csv.DictWriter(csvfile, fieldnames=['Filter'])
                w.writeheader()
                w.writerows([{'Filter':active_domain},{'Filter':' '}])
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
        context.update({'default_name': data, 'default_file_name': 'timesheet_overview_export' + time_csv})
        os.remove(csv_path)
        return context


    @api.multi
    def export_csv(self):
        """
        This function is use to export the timesheet overview records selected base on the filters
        """
        analytic_timesheet,active_domain = self.env['hr.analytic.timesheet'],False
        if self._context and 'active_model' in self._context and self._context['active_model'] == 'hr.analytic.timesheet':
            context = self._context.copy()
            active_domain = context.get('active_domain','')
            if active_domain:
                analytic_timesheet_records = analytic_timesheet.search(eval(str(active_domain)),order='account_id')
            else:
                analytic_timesheet_records = analytic_timesheet.browse(self._context['active_ids'])
            # print"analytic_timesheet_records----",analytic_timesheet_records
            context = self.export_csv_subfunction(analytic_timesheet_records,active_domain)

            return {
              'name': _('Exported Timsheet Overview'),
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'timesheet.overview.export',
              'type': 'ir.actions.act_window',
              'context': context,
              'target':'new',
            }
