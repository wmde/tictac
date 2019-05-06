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



class fte_records(models.Model):

    _name = 'fte.records'

    department_id = fields.Many2one('hr.department', string="Department")
    planned_fte = fields.Float(string='Planned FTE')
    fte =  fields.Float(string='FTE', digits=(5, 3))
    diff_fte = fields.Float(string='Difference FTE', digits=(5, 3))
    fte_id = fields.Many2one('fte.report', string="FTE Report")


class fte_report(models.Model):

    _name = 'fte.report'

    _order = 'id desc'

    name = fields.Date(string="Date", default=fields.Date.context_today)
    fte_ids = fields.One2many('fte.records', 'fte_id', string='FTE Records')


class res_company(models.Model):

    _inherit = "res.company"

    for_sow17 = fields.Boolean(string='Simulate date for leave calc')
    next_year_date = fields.Date('Next Year Date')

