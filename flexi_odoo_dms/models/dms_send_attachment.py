# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DmsSendAttachment(models.TransientModel):
    """
    Class to manage sending of attachments linked to models
    """
    _name = 'dms.send.attachment'
    _description = 'Upload Attachments to DMS'

    folder_id = fields.Many2one(comodel_name="dms.folder", string="Dossier de stockage",
                                help="Dossier de stockage", required=True)

    attachment_ids = fields.Many2many(comodel_name="ir.attachment", string="Fichiers joints", required=True,
                                      domain="[('res_model', '=', res_model), ('res_id', '=', res_id), "
                                             "('dms_file_code', '=', False), ('type','=','binary')]")


    res_model = fields.Char(string="Model name")

    res_id = fields.Integer(string="Res Id")

    @api.constrains('attachment_ids')
    def _check_attachment_ids(self):
        for rec in self:
            if not rec.attachment_ids:
                raise UserError(_("Attachments to upload should be provided"))
            attachments_type = rec.attachment_ids.mapped('type')
            if "binary" not in attachments_type or len(attachments_type) != 1:
                raise UserError(_("Only binary attachment are allowed"))

    def action_confirm(self):
        """
        Déclenche le processus après confirmation de ré-envoi
        """
        self.ensure_one()

        ctx_params = self._context.get('params', self._context)
        business_doc_id = ctx_params.get("id", ctx_params.get('active_id'))
        business_doc_name = ctx_params.get("model", ctx_params.get('active_model'))
        business_doc_obj = self.env[business_doc_name].browse(business_doc_id)
        if not business_doc_obj:
            raise UserError(_("Aucun document métier n'a été trouvé lors du renvoi du fichier sur la ged"))

        if not self.folder_id or not  self.attachment_ids:
            raise UserError(_("You should select folder and attachment for the upload"))
        # upload des fichier
        business_doc_obj.upload_to_dms(self.folder_id, self.attachment_ids)

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
