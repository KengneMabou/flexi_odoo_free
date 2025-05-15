# -*- coding: utf-8 -*-
from odoo import models, api
from odoo import tools


class IrMailServer(models.Model):

    _inherit = "ir.mail_server"

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
                   smtp_session=None):

        # Put Return-Path and Reply-To headers to be the sender to the mail
        del message['Return-Path']
        del message['Reply-To']

        all_from_emails = tools.email_split(message['From'])
        email_from = all_from_emails[0] if all_from_emails else message['From']
        message['Return-Path'] = email_from
        message['Reply-To'] = email_from

        # select an outgoing mail server related to the current smtp user and
        # force the smtp_session to be none to force odoo to generate a new
        # session with our outgoing mail server
        mail_server = self.sudo().search([('smtp_user','=',email_from)], order='sequence', limit=1)

        return super(IrMailServer, self).send_email(message, mail_server_id=mail_server.id,
                                                    smtp_server=smtp_server, smtp_port=smtp_port,
                                                    smtp_user=smtp_user, smtp_password=smtp_password,
                                                    smtp_encryption=smtp_encryption,
                                                    smtp_debug=smtp_debug, smtp_session=None)
