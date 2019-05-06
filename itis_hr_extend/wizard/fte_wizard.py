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


class create_fte(models.TransientModel):

    _name = 'create.fte'

    @api.model
    def check_parent(self, dep_dict, parent, pass_list):
        dep_env = self.env['hr.department']
        for dep in dep_env.browse(dep_dict.keys()):
            if dep.id not in pass_list:
                if dep.parent_id.id == parent:
                    return False
        return True

    @api.model
    def compute_child(self, dep, dep_dict, parent_list, pass_list):
#         print "dep_dict", dep_dict
        if dep.parent_id:
            # print parent_list,">>" , dep.name, ">>", dep.parent_id.name, '=', dep_dict.get(dep.id)
            if dep.parent_id.id not in parent_list:
                if not dep_dict.get(dep.parent_id.id):
                    dep_dict[dep.parent_id.id] = dep_dict.get(dep.id)
                else:
                    dep_dict[dep.parent_id.id] += dep_dict.get(dep.id)
                if dep_dict.get(dep.id) and self.check_parent(dep_dict, dep.parent_id.id, pass_list):
                    parent_list.append(dep.parent_id.id)
            else:
                dep_dict[dep.parent_id.id] = dep_dict.get(dep.id)
            self.compute_child(dep.parent_id, dep_dict, parent_list, pass_list)
        else:
            if not dep_dict.get(dep.parent_id.id):
                dep_dict[dep.id] = dep_dict.get(dep.id)
            else:
                dep_dict[dep.id] += dep_dict.get(dep.id)
        return dep_dict, parent_list




    @api.model
    def calc_fte(self, dep_dict):
        dep_env = self.env['hr.department']
        parent_list = []
        pass_list = []
        for dep in dep_env.browse(dep_dict.keys()):
            pass_list.append(dep.id)
            dep_dict, parent_list = self.compute_child(dep, dep_dict, parent_list, pass_list)
            # print "dep_dict", dep_dict
        return dep_dict

    @api.multi
    def generate_fte_report(self):
        department_env = self.env['hr.department']
        employee_env = self.env['hr.employee']
        dep_dict = {}
        for emp in employee_env.search([]):
#             print emp.fte, emp.name
            for fte in emp.fte_ids:
                if not dep_dict.get(fte.department_id.id):
                    dep_dict[fte.department_id.id] = (fte.fte/100) * emp.fte
                else:
                    dep_dict[fte.department_id.id] += (fte.fte/100) * emp.fte
        fte_list = []
        dep_dict = self.calc_fte(dep_dict)
        for dep in department_env.search([]):

            vals = {
                'department_id': dep.id,
                'planned_fte': dep.planned_fte,
                'fte': dep_dict.get(dep.id, 0.0),
                'diff_fte': dep.planned_fte - dep_dict.get(dep.id, 0.0)
            }
            fte_list.append((0,0,vals))
        fte = self.env['fte.report'].create({'fte_ids': fte_list})

        fte_view = self.env.ref('itis_hr_extend.itis_fte_report_form', False)
        return {
            'name': _('FTE Report'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fte.report',
            'views': [(fte_view.id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id':fte.id
        }
