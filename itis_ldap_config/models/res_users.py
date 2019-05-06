from openerp import tools
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager


class users(osv.osv):
    _inherit = "res.users"
    def _login(self, db, login, password):
        user_id = super(users, self)._login(db, login, password)
        # print"user_id-------",user_id
        registry = RegistryManager.get(db)
        with registry.cursor() as cr:
            ldap_obj = registry.get('ldap.record')
            context={'user_id':user_id}
            # ldap_obj.configure_ldap_user_subfunction(cr,SUPERUSER_ID,user_id,context)
        return user_id
