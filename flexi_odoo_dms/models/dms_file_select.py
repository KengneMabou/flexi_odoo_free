# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class DmsFileSelect(models.TransientModel):
    """
    Classe transient pour gérer la sélection des fichiers par l'utilisateur
    """
    _name = 'dms.file.select'
    _description = 'Sélection de fichiers DMS'

    file_ids = fields.Many2many(
        comodel_name="dms.file",
        relation="dms_file_select_rel",
        column1="wizard_id",
        column2="file_id",
        string="Fichiers sélectionnés",
        help="Fichiers choisis par l'utilisateur",
        required=True
    )

    def action_select_files(self):
        """
        Déclenche le processus après la sélection des fichiers
        """
        self.ensure_one()

        dms_callback = self._context.get('dms_callback', '')

        ctx_params = self._context.get('params', {})
        business_doc_id = self._context.get('active_id') or ctx_params.get("active_id") or ctx_params.get("id")
        business_doc_name = self._context.get('active_model') or ctx_params.get("active_model") or ctx_params.get("model")

        if not business_doc_id or not business_doc_name:
            raise UserError(_("Aucun document métier n'a été trouvé lors du processus "
                              "de sélection des fichiers sur la ged"))
            
        business_doc_obj = self.env[business_doc_name].browse(business_doc_id)
    
        try:
            return getattr(business_doc_obj, dms_callback)(self.file_ids, business_doc_name, business_doc_id)
        except Exception as e:
            raise UserError(_("Programming error: %s", e.args[0]))