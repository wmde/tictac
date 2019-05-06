# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_timesheet_line(osv.osv):
    _inherit = "hr.analytic.timesheet"

    # Add a column for ldap modifications records
    _columns = {
        'for_ldap_modification': fields.boolean('For Ldap Modification'),
        }

    # def _check(self, cr, uid, ids):
    #     for att in self.browse(cr, uid, ids):
    #         # print"for  ldap,sheet id----",att.for_ldap_modification,att.sheet_id
    #         if att.sheet_id and att.sheet_id.state not in ('draft', 'new') and not att.for_ldap_modification:#do not give a warning for ldap modify records
    #             raise osv.except_osv(_('Error!'), _('You cannot modify an entry in a confirmed timesheet.'))
    #     return True