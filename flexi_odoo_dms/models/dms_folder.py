# -*- coding: utf-8 -*-

from odoo import models, fields


class DmsFolder(models.TransientModel): 
    _name = 'dms.folder'
    _description = "Dms folder"

    name = fields.Char(string='Nom')
    parent_id = fields.Many2one(comodel_name='dms.folder', string='Dossier parent')
    folder_code = fields.Char(string='Folder code on DMS')
    last_modified_date = fields.Datetime(string='Date de dernière modification')
    size = fields.Integer(string='Taille (octets)')
    path = fields.Char(string='Chemin du dossier')
    

