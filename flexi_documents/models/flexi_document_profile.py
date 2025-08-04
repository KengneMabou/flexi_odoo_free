# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FlexiDocumentProfile(models.Model):

    _name = 'flexi.document.profile'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Profil d'accès aux documents"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"

    parent_id = fields.Many2one(comodel_name='flexi.document.profile', required=False, string='Profil parent',
                                ondelete='restrict', index=True, copy=False, tracking=True)

    parent_path = fields.Char(index=True, unaccent=False)

    child_ids = fields.One2many(string='Sous profils', comodel_name='flexi.document.profile',
                                inverse_name='parent_id')

    name = fields.Char(string="Nom", required=True, tracking=True, )

    complete_name = fields.Char(sring='Nom complet', compute='_compute_complete_name',
                                recursive=True, store=True)

    user_ids = fields.Many2many(comodel_name="res.users", string="Utilisateurs autorisés",
                                help="Utilisateurs du profil",
                                tracking=True)

    company_id = fields.Many2one(comodel_name='res.company', string="Société",
                                 tracking=True, ondelete='restrict',
                                 default=lambda self: self.env.user.company_id.id)

    def get_complete_user_ids(self):
        """"Utilisateurs du profil courant ainsi que des profils parents"""
        result = self.env['res.users']
        for rec in self:
            current_profil = rec
            while current_profil:
                result |= current_profil.user_ids
                current_profil  = current_profil.parent_id
        return result



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
            raise ValidationError(_('You cannot create recursive profile.'))

    @api.constrains('name')
    def _check_profile_name(self):
        for rec in self:
            prev_records = self.env['flexi.document.profile'].search([]).\
                filtered(lambda profile: profile.name.lower() == rec.name.lower())

            if len(prev_records) > 1:
                raise ValidationError(_("Deux profils ne peuvent pas avoir le nom. Les noms "
                                        "sont insensibles à la casse (Par exemple 'Achats', 'achats' ou "
                                        "'ACHATS' considérés comme équivalentes"))
