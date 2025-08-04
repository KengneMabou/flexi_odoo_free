# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DmsFile(models.TransientModel):
    _name = 'dms.file'
    _description = "Dms file"

    name = fields.Char(string='Nom du fichier', required=True)
    folder_path = fields.Char( string='Chemin du dossier parent', required=True)
    file_code = fields.Char(string='File code on DMS')
    content = fields.Binary(string='Contenu du fichier')
    path = fields.Char(string='Chemin du fichier')
    size = fields.Integer(string='Taille (octets)', compute='_compute_size')
    last_modified_date = fields.Datetime(string='Date de dernière modification')

    @api.depends('content')
    def _compute_size(self):
        for record in self:
            record.size = len(record.content) if record.content else 0