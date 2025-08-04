# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FlexiDocumentFolder(models.Model):

    _name = 'flexi.document.folder'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Dossier de document"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"

    parent_id = fields.Many2one(comodel_name='flexi.document.folder', required=False, string='Dossier parent',
                                ondelete='restrict', index=True, copy=False, tracking=True)

    parent_path = fields.Char(index=True, unaccent=False)

    child_ids = fields.One2many(string='Sous dossiers', comodel_name='flexi.document.folder',
                                inverse_name='parent_id')

    name = fields.Char(string="Nom", required=True, tracking=True, )

    complete_name = fields.Char(sring='Nom complet', compute='_compute_complete_name',
                                recursive=True, store=True)

    company_id = fields.Many2one(comodel_name='res.company', string="Société",
                                 tracking=True, ondelete='restrict',
                                 default=lambda self: self.env.user.company_id.id)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for record in self:
            if record.parent_id:
                record.complete_name = '%s / %s' % (record.parent_id.complete_name, record.name)
            else:
                record.complete_name = record.name

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive folder.'))

    @api.constrains('name')
    def _check_folder_name(self):
        for rec in self:
            prev_records = self.env['flexi.document.folder'].search([]).\
                filtered(lambda folder: folder.name.lower() == rec.name.lower())

            if len(prev_records) > 1:
                raise ValidationError(_("Deux dossiers ne peuvent pas avoir le nom. Les noms "
                                        "sont insensibles à la casse (Par exemple 'Achats', 'achats' ou "
                                        "'ACHATS' considérés comme équivalentes"))
