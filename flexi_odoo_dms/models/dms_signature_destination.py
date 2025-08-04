# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DmsSignatureDestination(models.TransientModel):
    _name = 'dms.signature.destination'
    _description = 'Destination de Signature DMS'

    signature_request_id = fields.Many2one(
        comodel_name='dms.signature.request',
        string='Demande de Signature',
        required=True
    )
    
    email = fields.Char(string='Email', compute='_compute_email')

    internal_contact_ref = fields.Reference(string="Contact interne",
                                            selection=[('res.partner','Patenaire'),
                                                       ('hr.employee','Employee'),
                                                       ('res.users', 'Utilisateur'),
                                                   ],
                                            tracking=True,required=True)

    @api.depends("internal_contact_ref")
    def _compute_email(self):
        for record in self:
            if record.internal_contact_ref:
                if 'email' in record.internal_contact_ref:
                    record.email = record.internal_contact_ref.email 
                elif 'work_email' in record.internal_contact_ref:
                    record.email = record.internal_contact_ref.work_email
                else:
                    record.email = ""
            else:
                record.email = ""
