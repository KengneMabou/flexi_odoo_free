# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
import re


class DmsSignatureRequest(models.TransientModel):

    _name = 'dms.signature.request'
    _description = 'Demande de signature DMS'

    email_addresses = fields.Char(string='Adresses Email', required=False, help="Une ou plusieurs adresses "
                                                                               "séparées par une virgule")

    signature_destination_ids = fields.One2many(comodel_name='dms.signature.destination',
                                                inverse_name='signature_request_id',
                                                string='Destinations de Signature'
                                                )

    def send_signature_request(self):
        """
        Envoie la demande de signature aux destinataires.
        """
        self.ensure_one()
        # Liste pour stocker toutes les adresses email valides
        valid_emails = []
        # Vérifier si l'utilisateur a saisi des adresses email dans le champ principal
        if self.email_addresses:
            # Séparer les adresses email saisies (séparées par des virgules)
            valid_emails.extend([email.strip() for email in self.email_addresses.split(',')])
            # Valider chaque adresse email
        # récupérer les adresses de destination supplémentaires provenant des modèles de contact
        valid_emails.extend(self.signature_destination_ids.mapped('email'))
        for email in valid_emails:
            if email:  # Vérifier que l'email n'est pas vide
                # Validation  du format d'email
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                    raise UserError(_("Format d'adresse email invalide: %s") % email)

        ctx_params = self._context.get('params', self._context)
        business_doc_id = ctx_params.get("id", ctx_params.get('active_id'))
        business_doc_name = ctx_params.get("model", ctx_params.get('active_model'))
        business_doc_obj = self.env[business_doc_name].browse(business_doc_id)
        if not business_doc_obj:
            raise UserError(_("Aucun document métier n'a été trouvé lors du renvoi du fichier sur la ged"))

        business_doc_obj.send_to_signature_server(valid_emails)