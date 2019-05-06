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

from openerp import models, api, fields, _, osv

class SignInTask(models.TransientModel):

    _name = "sign.in.task"

    analytic_account_id = fields.Many2one("account.analytic.account", "Analytic Account")
    service_desc_id = fields.Many2one('service.description',string="Service Desc")
    emp_comment = fields.Text("Comment")

    @api.multi
    def set_task(self):
        return True

    @api.multi
    def do_entry_timesheet(self):
        timesheet_id = False
        if self.analytic_account_id.id:
            timesheet_obj = self.pool.get('hr.analytic.timesheet')
            cr = self.env.cr
            uid = self.env.uid
            emp_obj = self.env['hr.employee']
            hour = 0.0
            res = timesheet_obj.default_get(cr, uid, ['product_id','product_uom_id'])

            if not res['product_uom_id']:
                raise osv.except_osv(_('User Error!'), _('Please define cost unit for this employee.'))
            up = timesheet_obj.on_change_unit_amount(cr, uid, False, res['product_id'], hour,False, res['product_uom_id'])['value']
            res['name'] = "From Time Tracker"
            res['account_id'] = self.analytic_account_id.id
            res['unit_amount'] = hour
            res['service_desc_id'] = self.service_desc_id.id
            res['emp_comment'] = self.emp_comment
            emp_journal = emp_obj.search([('user_id', '=', self.env.uid)]).journal_id
            res['journal_id'] = emp_journal and emp_journal.id or False
            res.update(up)
            up = timesheet_obj.on_change_account_id(cr, uid, [], res['account_id']).get('value', {})
            res.update(up)
            timesheet_id = timesheet_obj.create(cr, uid, res)
        return timesheet_id
