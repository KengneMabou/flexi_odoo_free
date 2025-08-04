# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class DmsSignatureConfirm(models.TransientModel):
    _name = 'dms.signature.confirm'
    _description = 'Confirmation de nouvelle demande de signature'
    
    name = fields.Char(string=' Message de confirmation', readonly=True,
                       default='Ce fichier a déjà été envoyé en signature, voulez-vous le renvoyer ?'
                       )

    def action_confirm(self):
        """
        Déclenche le processus après confirmation de renvoi
        """
        self.ensure_one()
        ctx_params = self._context.get('params', self._context)
        business_doc_id = ctx_params.get("id", ctx_params.get('active_id'))
        business_doc_name = ctx_params.get("model", ctx_params.get('active_model'))
        business_doc_obj = self.env[business_doc_name].browse(business_doc_id)

        if not business_doc_obj:
            raise UserError(_("Aucun document métier n'a été trouvé lors du renvoi du fichier sur la GED"))

        # Ouvrir la requete de signature
        return business_doc_obj.open_signature_request_wizard()

    def action_cancel(self):
        """
        Action d'annulation
        """
        return {
            'type': 'ir.actions.act_window_close'
        }
