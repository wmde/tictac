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


class HRConfig(models.TransientModel):

    _inherit = "hr.config.settings"

    leave_account_id = fields.Many2one("account.analytic.account", "Analytic Account for Leave")
    ot_leave_account_id = fields.Many2one("account.analytic.account", "Analytic Account for Overtime Leave")

    @api.multi
    def set_ot_leave_account_id(self):
        self.env.user.company_id.write({
            "leave_account_id": self.leave_account_id.id,
            "ot_leave_account_id": self.ot_leave_account_id.id,
        })
        return True

    @api.model
    def default_get(self, fields):
        la_id = self.env.user.company_id.leave_account_id.id or False
        ola_id = self.env.user.company_id.ot_leave_account_id.id or False
        res = super(HRConfig, self).default_get(fields)
        res.update({
            "leave_account_id": la_id,
            "ot_leave_account_id": ola_id,
        })
        return res

class ResCompany(models.Model):

    _inherit = "res.company"

    leave_account_id = fields.Many2one("account.analytic.account", "Analytic Account for Leave")
    ot_leave_account_id = fields.Many2one("account.analytic.account", "Analytic Account for Overtime Leave")
