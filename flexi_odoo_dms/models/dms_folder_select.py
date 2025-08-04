# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DmsFolderSelect(models.TransientModel):
    """
    Classe transient pour gérer la sélection des dossiers par l'utilisateur
    """
    _name = 'dms.folder.select'
    _description = 'Sélection de dossiers Nextcloud'

    folder_id = fields.Many2one(
        comodel_name="dms.folder", 
        string="Dossier sélectionné",
        help="Dossier choisi par l'utilisateur",
        required=True
    )

    def action_select_folder(self):
        """
        Déclenche le processus après la sélection du dossier
        """
        self.ensure_one()
        
        dms_callback = self._context.get('dms_callback','')

        ctx_params = self._context.get('params', {})
        business_doc_id = self._context.get('active_id') or ctx_params.get("active_id") or ctx_params.get("id")
        business_doc_name = self._context.get('active_model') or ctx_params.get("active_model") or ctx_params.get("model")

        if not business_doc_id or not business_doc_name:
            raise UserError(_("Aucun document métier n'a été trouvé lors du processus de selection du dossier sur la ged"))
            
        business_doc_obj = self.env[business_doc_name].browse(business_doc_id)

        try:
            getattr(business_doc_obj, dms_callback)(self.folder_id, business_doc_name, business_doc_id)
            file_upload_callback = self._context.get('file_upload_callback',False)
            if file_upload_callback:
                return getattr(business_doc_obj, file_upload_callback)()

        except Exception as e:
            raise UserError(_("Programming error: %s", e.args[0]))

