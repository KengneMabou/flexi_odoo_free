# -*- coding: utf-8 -*-
from odoo import models, api
from odoo import tools


class MailMail(models.Model):

    _inherit = "mail.mail"

    @api.model_create_multi
    def create(self, vals_list):
        result = super(MailMail, self).create(vals_list)
        result.force_default_out_mail_server()
        return result

    def send(self):
        self.force_default_out_mail_server()
        return super(MailMail, self).send()

    def force_default_out_mail_server(self):
        for record in self:
            if not record.mail_server_id:
                all_from_emails = tools.email_split(record.email_from)
                email_from = all_from_emails[0] if all_from_emails else record.email_from
                mail_server = self.env['ir.mail_server'].sudo().\
                    search([('smtp_user', '=', email_from)], order='sequence desc', limit=1)
                if mail_server:
                    record.mail_server_id = mail_server.id

