# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    archive_expired_documents = fields.Boolean(string="Archiver automatiquement les documents expirés",
                                                   default=True, tracking=True)

    max_expiry_notification = fields.Integer(string="Nombre max de notification d'expiration",
                                               default=1, tracking=True)

    document_profile_heritage = fields.Selection(selection=[('hierarchy', 'Toute la hiérarchie'),
                                                            ('current','Profile courant'),
                                                            ],
                                                 string="Héritage de profils", default="current",
                                                 tracking=True)

    @api.constrains('max_expiry_notification')
    def _check_max_expiry_notification(self):
        for rec in self:
            if rec.max_expiry_notification < 1:
                raise ValidationError(_("Le nombre max de notification d'expiration doit être strictement "
                                        "positif"))
