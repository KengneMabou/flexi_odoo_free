# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class DmsFileConfirm(models.TransientModel):
    """
    Classe transient pour confirmer le renvoi du fichier par l'utilisateur
    """
    _name = 'dms.file.confirm'
    
    _description = 'confirmation de renvoi du fichier'

    name = fields.Char(
        string=' Message de confirmation', 
        readonly=True, 
        default='Ce fichier a déjà été envoyé sur la GED, voulez-vous le renvoyer ?'
    )

    def action_confirm(self):
        """
        Déclenche le processus après confirmation de réenvoi
        """
        self.ensure_one()
        dms_folder_id = self._context.get('dms_folder_id')
        dms_folder_obj = self.env['dms.folder'].browse(dms_folder_id)
        
        if not dms_folder_obj:
            raise UserError(_("Aucun dossier GED n'a été trouvé lors du processus de confirmation"))

        ctx_params = self._context.get('params', self._context)
        business_doc_id = ctx_params.get("id", ctx_params.get('active_id'))
        business_doc_name = ctx_params.get("model", ctx_params.get('active_model'))
        business_doc_obj = self.env[business_doc_name].browse(business_doc_id)
        if not business_doc_obj:
            raise UserError(_("Aucun document métier n'a été trouvé lors du renvoi du fichier sur la ged"))
        
        # Renvoi du fichier
        business_doc_obj.upload_to_dms(dms_folder_obj)

        return {
            'type': 'ir.actions.act_window_close'
        }


    def action_cancel(self):
        """
        Action d'annulation
        """
        return {
            'type': 'ir.actions.act_window_close'
        }
