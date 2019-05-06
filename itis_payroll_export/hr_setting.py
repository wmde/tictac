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


class hr_config(models.TransientModel):

    _inherit = "hr.config.settings"

    sick_account_id = fields.Many2one("account.analytic.account", "Sick Account")

    @api.multi
    def set_sick_account_id(self):
        self.env.user.company_id.write({
            "sick_account_id": self.sick_account_id.id,
        })
        return True

    @api.model
    def default_get(self, fields):
        sick_id = self.env.user.company_id.sick_account_id.id or False
        res = super(hr_config, self).default_get(fields)
        res.update({
            "sick_account_id": sick_id,
        })
        return res


class res_company(models.Model):

    _inherit = "res.company"

    sick_account_id = fields.Many2one("account.analytic.account", "Sick Account")

