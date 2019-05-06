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


class employee_report(models.TransientModel):

    _name = 'employee.report'

    def _get_employee(self):
        user_env = self.env['res.users']
        emp_env = self.env['hr.employee']
        emp_rec = emp_env.search([('user_id', '=', self._uid)])
        if not len(emp_rec):
            raise Warning(_("No associated employee found with user"))
        if len(emp_rec) > 1:
            raise Warning(_("User is associated with multiple employee"))
        emp_rec = emp_rec[0]
        emp_list = []
        for emp in emp_env.search(['|', ('parent_id', '=', emp_rec.id), ('id', '=', emp_rec.id)]):
            emp_val = {
                'employee_id': emp.id,
                'overtime_count':emp.employee_overtime_id.emp_overtime_count,
                # 'overtime_count':emp.overtime_count,
                'sum_leaves': emp.sum_leaves,
                'sum_leaves_ny':emp.sum_leaves_ny #for SOW17
            }
            if emp_val['overtime_count'] <= 20 and emp_val['overtime_count'] >= -20:
                color = "green"
            elif emp_val['overtime_count'] <= 40 and emp_val['overtime_count'] >= -40:
                color = "yellow"
            else:
                color = "red"
            emp_val['color'] = color
            emp_list.append((0, 0, emp_val))
        return emp_list

    name= fields.Date(string="Date", default=fields.Date.context_today)
    employee_ids = fields.One2many('employee.report.data', 'employee_report_id', string='Employees', default=_get_employee)


class employee_report_data(models.TransientModel):

    _name = 'employee.report.data'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    overtime_count = fields.Float(string='Overtime Count')
    sum_leaves = fields.Float(string='Gesamtanspruch')
    sum_leaves_ny = fields.Float(string='Next Year Remaining Leaves')#for SOW17
    employee_report_id = fields.Many2one('employee.report', string='Employee Report')
    color = fields.Char()
