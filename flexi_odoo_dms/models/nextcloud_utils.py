# -*- coding: utf-8 -*-

import logging
import base64
import nc_py_api
import os
import tempfile
from datetime import datetime
from odoo import _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


# Helpers functions to integrate with nextcloud

def build_full_url(http_base_domain, url_path):
    if not http_base_domain or not  url_path or not isinstance(http_base_domain, str) \
            or not isinstance(url_path, str):
        raise UserError(_("Invalid parameters to build dms full path for documents"))

    while http_base_domain[-1] == "/":
        http_base_domain = http_base_domain[:-1]

    return http_base_domain + url_path



def _get_nextcloud_client(odoo_user):
    """
    Initialise (à partir une instance odoo de res_users) et retourne un client Nextcloud

    Returns:
        nextcloud_client.Client: Client Nextcloud configuré
    """
    try:
        nc = nc_py_api.Nextcloud(nextcloud_url=odoo_user.nextcloud_url, nc_auth_user=odoo_user.nextcloud_login,
                                 nc_auth_pass=odoo_user.nextcloud_passwd)
        return nc
    except Exception as e:
        logging.error(f"Erreur de connexion Nextcloud : {e}")
        return None


def convert_datetime(tz_date):
    return tz_date.replace(tzinfo=None)


def get_nextcloud_folders(odoo_user):
    """
    Fonction pour obtenir la liste des dossiers de nextcloud
    
    """
    # create Nextcloud client instance class
    nc = _get_nextcloud_client(odoo_user)

    # recupère la liste de tous les dossiers du compte utilisateur sur la ged
    try:
        nc_folders = [i for i in nc.files.listdir(depth=-1) if i.is_dir]
        odoo_folders = []
        for folder in nc_folders:
            folder_info = {
                'folder_code': folder.file_id,
                'name': folder.name,
                'path': folder.user_path,
                'last_modified_date': convert_datetime(folder.info.last_modified),
                'size': int(folder.info.size)
            }
            odoo_folders.append(folder_info)
        return odoo_folders
    except Exception as e:
        raise UserError(_("Unable to get Nextcloud folders: %s", e.args[0]))


def upload_to_nextcloud(odoo_user, nc_file_path, local_file_path):
    
    nc = _get_nextcloud_client(odoo_user)
    try:
        return nc.files.upload_stream(nc_file_path , local_file_path)
    except Exception as e:
        raise UserError(_("Unable to upload file to Nextcloud: %s", e.args[0]))


def delete_on_nextcloud(odoo_user, nc_file_path):
    
    nc = _get_nextcloud_client(odoo_user)
    try:
        nc.files.delete(nc_file_path)
    except Exception as e:
        raise UserError(_("Unable to delete file on Nextcloud: %s", e.args[0]))


def get_nextcloud_files(odoo_user, folder_obj):
    """
    Récupère les fichiers d'un dossier spécifique
    """
    nc = _get_nextcloud_client(odoo_user)
    
    try:
        # Liste uniquement les éléments du dossier spécifié
        
        files = nc.files.listdir(folder_obj.path)
        
        files_list = []
        for item in files:
            # On ne prend que les fichiers, pas les dossiers
            if not item.is_dir:
                file_info = {
                    'file_code': item.file_id,
                    'name': item.name,
                    'folder_path': folder_obj.path,
                    'path': item.user_path,
                    'last_modified_date': convert_datetime(item.info.last_modified),
                    'size': int(item.info.size),
                }
                files_list.append(file_info)
                
        return files_list
        
    except Exception as e:
        raise UserError(_("Impossible de récupérer les infos des fichiers : %s", e.args[0]))


def get_nextcloud_content(odoo_user, file_obj, b64=True, chunk=True):
    """
    Récupère le contenu d'un fichier spécifique
    """
    nc = _get_nextcloud_client(odoo_user)
    
    try:
        # téléchargement du fichier
        file_content = None
        if not chunk:
            file_content = nc.files.download(file_obj.path)
        else:
            # Création d'un dossier temporaire pour stocker le fichier
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
            # Génération du nom de fichier basé sur le modèle et l'ID
            filename = f"{file_obj._name.replace('.', '_')}_{file_obj.id}_{timestamp}"
            temp_file_path = os.path.join(temp_dir, filename)

            nc.files.download2stream(file_obj.path, temp_file_path)

            with open(temp_file_path, 'rb') as fp:
                file_content = fp.read()

        if not file_content:
            return False
        
        return base64.b64encode(file_content) if b64 else file_content
        
    except Exception as e:
        raise UserError(_("Impossible de récupérer le contenu des fichiers : %s", e.args[0]))


    

   