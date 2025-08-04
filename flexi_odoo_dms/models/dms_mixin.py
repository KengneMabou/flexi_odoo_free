# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
import logging
import os
import tempfile
from datetime import datetime
import json
import requests
from .nextcloud_utils import get_nextcloud_folders, upload_to_nextcloud, delete_on_nextcloud, \
    get_nextcloud_files, get_nextcloud_content, build_full_url
_logger = logging.getLogger(__name__)


class DmsMixing(models.AbstractModel):
    """Classe abstraite pour l'intégration d'odoo avec les solutions Ged(Nextcloud, Alfresco,Google drive,...)
    ."""
    _name = 'dms.mixin'
    _description = 'intégration odoo avec les solutions Ged'
    
    dms_file_reference = fields.Char(string="reference du fichier sur la ged",)
    dms_file_path = fields.Char(string="chemin du fichier sur la ged",)
    already_sent_to_signature = fields.Boolean(string="Fichier déjà envoyé en  signature")

     ###################################################################################################
    # Méthodes du premier cas d'utilisation: envoyer le fichier d'un document métier à la Ged
    ##################################################################################################

    def upload_report_file_to_dms(self): 
        """
        Fonction point d'entée pour l'envoi de document  à la GED
        
        """ 
        self.ensure_one()      
        self.verify_dms_group()
        return self.get_dms_folders('verify_dms_reference')

    def verify_dms_group(self):
        """
        Verifie que l'utilisateur courant appartient au groupe d'access à la GED
        
        Raise: UserError
        """

        if not self.env.user.has_group('nasara_odoo_dms.group_dms_manager'):
            raise UserError(_("Vous n'avez pas les droits d'accès nécessaire pour stocker un document la ged"))  

    def get_dms_folders(self, callback:str):
        """
        Fonction pour obtenir la liste des dossiers
        
        """
        self.download_dms_folders()
       
        return self.open_user_selection_wizard(callback, 'nasara_odoo_dms.act_open_dms_folder_select_view')

    def open_user_selection_wizard(self, callback:str, wizard_action:str):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(wizard_action)
        current_context = action.setdefault('context',{})
        if isinstance(current_context, str):
            current_context = json.loads(current_context)

        current_context.update(self._context)
        current_context.update({"dms_callback": callback})
        # current_context.update({"active_model": self._context.get('active_model'), "active_id":self._context.get('active_id'), "dms_callback": callback})
        action['context'] = current_context
        return action

    def open_confirm_file_upload(self, folder_obj, source_model, source_id):
        self.ensure_one()
        confirm_file_form = self.env.ref("nasara_odoo_dms.view_dms_file_confirm_form")
        return {
                'type': 'ir.actions.act_window',
                'name': "Confirmation de l'envoie du fichier sur la ged",
                'res_model': 'dms.file.confirm',
                'view_mode': 'form',
                'view_id': confirm_file_form.id, 
                'target': 'new',
                'context': {
                    'dms_folder_id': folder_obj.id,
                    'active_id': source_id,
                    'active_model': source_model
                },     
            }
    

    def verify_dms_reference(self, folder_obj, source_model, source_id):
        # Vérifier si le fichier n"a pas été préalablement stocké sur la ged
        self.ensure_one()
        if not self.dms_file_reference:
            self.upload_to_dms(folder_obj)
        else :
            return self.open_confirm_file_upload(folder_obj, source_model, source_id)


    def upload_to_dms(self, folder_obj):
         # Code pour téléverser le PDF vers la ged
        self.ensure_one()
        if self.dms_file_reference or self.dms_file_path:
            self.delete_on_dms(file_id=self.dms_file_reference, file_path=self.dms_file_path)
        local_file_path = self.generate_pdf_from_erp()
        nc_file_path = os.path.join(folder_obj.path, os.path.basename(local_file_path))
        dms_file = upload_to_nextcloud(self.env.user, nc_file_path, local_file_path)
        self.dms_file_reference = str(dms_file.file_id)
        self.dms_file_path = str(dms_file.user_path)



    def generate_pdf_from_erp(self):
        # Code pour générer le PDF depuis les informations de l'ERP et retourner l"instance du fichier
        # ou le chemin du fichier. Utiliser les fichiers tempoaraires python

        self.ensure_one()

        # Création d'un dossier temporaire pour stocker le PDF
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
        # Génération du nom de fichier basé sur le modèle et l'ID
        filename = f"{self._name.replace('.', '_')}_{self.id}_{timestamp}.pdf"
        temp_file_path = os.path.join(temp_dir, filename)
    
        # Identification du rapport en fonction du modèle
        report_name = {
            'sale.order': 'sale.action_report_saleorder',
            'purchase.order': 'purchase.action_report_purchase_order',
            'hr.payslip': 'payroll.action_report_payslip',
            'account.move': 'account.account_invoices',
        }.get(self._name)
    
        if not report_name:
            raise UserError(_("Aucun modèle de rapport trouvé pour ce type de document"))
    
        # Génération du PDF
        report = self.env.ref(report_name)
        pdf_content = self.env['ir.actions.report']._render_qweb_pdf(report, res_ids=self.id)[0]
    
        # Écriture du PDF dans le fichier temporaire
        with open(temp_file_path, 'wb') as pdf_file:
            pdf_file.write(pdf_content)
    
        return temp_file_path


    def delete_on_dms(self, file_id=None, file_path=None):
        # Code pour supprimer le fichier dans la ged
        if not file_id and not file_path:
            raise UserError(_("veuillez fournir l'identifiant ou le chemin du fichier sur la ged"))
            
        if file_path:
            delete_on_nextcloud(self.env.user, file_path)



    ##################################################################################################
    # Méthodes du deuxième cas d'utilisation: associer un fichier de la Ged à un document métier de l'erp
    ##################################################################################################


    def demande_association_fichier(self):
        # Point d"entrée de la demande d'association du fichier de la Ged au document métier
        self.ensure_one()      
        self.verify_dms_group()
        return self.get_dms_folders('choix_dossiers_confirmation')

    def get_dms_files(self, folder_obj, callback:str):
        """
        Fonction pour obtenir la liste des fichiers
        
        """

        # recupère la liste de tous les fichiers du compte utilisateur sur la ged
        all_files = get_nextcloud_files(self.env.user, folder_obj)
        self.env["dms.file"].create(all_files)
        return self.open_files_selection_wizard(callback)

    def choix_dossiers_confirmation(self, folder_obj, source_model, source_id):
        """Réutilise la logique de vérification existante"""
    
        # Récupérer sur nextcloud les fichiers contenu dans le dossier folder_obj passé en paramètre et 
        # ensuite retourner un wizard qui affiche cette la liste des fichiers récupérer dans un champ many2many
        self.ensure_one()
        #propager le modèle et l'id initial  
        self = self.with_context(active_id=source_id, active_model=source_model)
        return self.get_dms_files(folder_obj, "associer_fichiers_document_metier") 
    
    
    def open_files_selection_wizard(self, callback:str):
        """
        Ouvre le wizard de selection et confirmation des fichiers à associer
        """
        return self.open_user_selection_wizard(callback, 'nasara_odoo_dms.act_open_dms_files_select_view')

    def associer_fichiers_document_metier(self, files_obj, source_model, source_id):
        """ Fonction appelée depuis le wizard de selection des fichiers. 
        Elle permet une association définitive des fichiers de GED sélectionnés au document métier. 
        On utilisera pour celà le modèle ir.attachment dont on créera une instance lié au moèle 
        source_model et à l'id source_id
        """
        if not files_obj or not source_model or not source_id:
            return False
            
        IrAttachment = self.env['ir.attachment']
        created_attachments = []
        
        for file_record in files_obj:
            # Vérifie si le fichier existe déjà comme pièce jointe et la supprimer
            existing_attachment = IrAttachment.search([
                ('res_model', '=', source_model),
                ('res_id', '=', source_id),
                ('dms_file_code', '=', file_record.file_code),
            ], limit=1)
            
            if existing_attachment:
                existing_attachment.sudo().unlink()

            attachment_vals = {
                'name': file_record.name,
                'res_model': source_model,
                'res_id': source_id,
                'dms_file_code': file_record.file_code,  # ID du fichier stocké
                'description': f"Fichier GED: {file_record.folder_path} -- {file_record.path}",
            }

            if self.env.user.company_id.dms_download_type == 'url':
                attachment_vals['type'] = "url"
                attachment_vals['url'] = build_full_url(self.env.user.nextcloud_url, file_record.path)
            else:
                # Prépare les valeurs de la pièce jointe
                file_content = get_nextcloud_content(self.env.user, file_record, b64=True, chunk=True)
                attachment_vals['type'] = "binary"
                attachment_vals['datas'] = file_content,  # On prend le contenu télécharger

            
            # Crée la nouvelle pièce jointe
            new_attachment = IrAttachment.create(attachment_vals)
            created_attachments.append(new_attachment.id)
        
        return created_attachments
    

     ###################################################################################################
    # Méthodes du troisième cas d'utilisation: Signer le fichier d' un document métier sur la Ged à partir de l'Erp
    ##################################################################################################

    def demande_signature_document(self):
        """ Vérifie les droits de l'utilisateur et génère le document en PDF avant signature """
        self.ensure_one()
        self.verify_dms_group()
        if self.dms_file_reference:
            if self.already_sent_to_signature:
                return self.open_signature_confirmation_wizard()
            else:
                return self.open_signature_request_wizard()
        else:
            return self.with_context(file_upload_callback="open_signature_request_wizard").upload_report_file_to_dms()

    def open_signature_request_wizard(self):
        self.ensure_one()
        signature_request_form = self.env.ref("nasara_odoo_dms.view_dms_signature_request_form")
        return {
            'type': 'ir.actions.act_window',
            'name': "Nouvelle demande de signature",
            'res_model': 'dms.signature.request',
            'view_mode': 'form',
            'view_id': signature_request_form.id,
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name
            },
        }  

    def open_signature_confirmation_wizard(self):
        self.ensure_one()
        confirm_signature_form = self.env.ref("nasara_odoo_dms.view_dms_signature_confirm_form")
        return {
            'type': 'ir.actions.act_window',
            'name': "Confirmation demande de signature",
            'res_model': 'dms.signature.confirm',
            'view_mode': 'form',
            'view_id': confirm_signature_form.id,
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name
            },
        }

    def send_to_signature_server(self, valid_emails: list):
        self.ensure_one()
        url = f"https://nextcloud.nasara-technologies.fr/apps/integration_docusign/docusign/standalone-sign/{self.dms_file_reference}"

        # Préparation des données pour la requête PUT
        data = {
            "targetEmails": valid_emails
        }

        try:
            # Envoi de la requête PUT avec la bibliothèque requests
            response = requests.put(url, data=data)
            if response.status_code in [401]:
                raise UserError(
                    _("Unable to send the file to signature server: %s", response.json().get('error', 'None')))
            self.already_sent_to_signature = True
        except Exception as net_err:
            raise UserError(
                _("Unable to contact the file to signature server for signing request: %s", net_err.args[0]))

    def open_attachments_upload_to_dms(self):

        if 'message_follower_ids' not in  self or 'message_ids' not in self or "activity_ids" not in self:
            raise UserError(_("Impossible to send attachments to DMS because there is no "
                              "mail thread mixin linked to this model"))

        self.download_dms_folders()
        dms_send_attachment_form = self.env.ref("nasara_odoo_dms.view_dms_send_attachment_form")
        return {
            'type': 'ir.actions.act_window',
            'name': "Attachments upload to dms",
            'res_model': 'dms.send.attachment',
            'view_mode': 'form',
            'view_id': dms_send_attachment_form.id,
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name
            },
        }

    def send_attachments_to_dms(self, dms_folder, attachments):
        self.ensure_one()
        IrAttachment = self.env['ir.attachment']
        for c_attach in attachments:
            local_file_path = c_attach._full_path(c_attach.store_fname)
            nc_file_path = os.path.join(dms_folder.path, os.path.basename(local_file_path))
            dms_file = upload_to_nextcloud(self.env.user, nc_file_path, local_file_path)

            if self.env.user.company_id.dms_download_type == 'url':
                attachment_vals = {
                    'name': dms_file.name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'dms_file_code': dms_file.file_code,  # ID du fichier stocké
                    'description': f"Fichier GED: {dms_file.folder_path} -- {dms_file.path}",
                    'type': 'url',
                    'url': build_full_url(self.env.user.nextcloud_url, dms_file.path),
                }
                # Crée la nouvelle pièce jointe sous forme d'url vers le serveur de stockage
                IrAttachment.create(attachment_vals)
                c_attach.sudo().unlink()

    def download_dms_folders(self):
        # recupère la liste de tous les dossiers du compte utilisateur sur la ged
        all_folders = get_nextcloud_folders(self.env.user)
        # _logger.info("============================= ici %s " % all_folders)
        folders_to_create = []
        for cfol in all_folders:
            if self.env['dms.folder'].search([('folder_code','=',cfol['folder_code'])]):
                folders_to_create.append(cfol)
        if folders_to_create:
            self.env["dms.folder"].create(all_folders)

