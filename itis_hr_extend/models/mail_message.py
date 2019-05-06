
from openerp import models, api, fields, _
from email.utils import formataddr


class mail_message(models.Model):
    _inherit = 'mail.message'
    
    @api.model
    def create(self, vals):
        # print"self._context.------",self._context
        # if self._context.get('holiday_create'):

        if self._context.get('hr_uid'):
            user = self.env['res.users'].browse(self._context.get('hr_uid'))

            if user.alias_name and user.alias_domain:
                from_address = formataddr((user.name, '%s@%s' % (user.alias_name, user.alias_domain)))
                vals.update({'email_from': from_address,'reply_to':from_address})
            elif user.email:
                from_address =  formataddr((user.name, user.email))
                vals.update({'email_from': from_address,'reply_to':from_address})

            vals.update({'author_id': user.partner_id.id})
        res = super(mail_message, self).create(vals)
        return res

