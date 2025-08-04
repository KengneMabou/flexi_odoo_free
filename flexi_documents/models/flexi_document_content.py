# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime


class FlexiDocumentContent(models.Model):

    _name = 'flexi.document.content'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Contenu de document"

    name = fields.Char(string="Intitulé", required=True, tracking=True,)

    visibility_type = fields.Selection(selection=[('only_me', 'Moi uniquement'),
                                                  ('all_users','Tous les utilisateurs'),
                                                  ('selected_users','Utilisateurs choisis'),
                                                  ('selected_profiles','Utilisateurs des profils choisis')],
                                       string="Visibilité", required=True, tracking=True)

    selected_user_ids = fields.Many2many(comodel_name="res.users", string="Utilisateurs choisies",
                                           help="Utilisateurs choisies pour accéder au document",
                                           tracking=True, relation="selected_user_for_content_rel")

    selected_profile_ids = fields.Many2many(comodel_name="flexi.document.profile", string="Profils choisis",
                                         help="Profils choisis pour accéder au document",
                                         tracking=True, )

    visibility_user_ids = fields.Many2many(comodel_name="res.users", string="Utilisateurs autorisés",
                                           help="Utilisateurs autorisés à accéder au document",
                                           tracking=True, readonly=True, relation="visibility_user_for_content_rel")

    attachment_ids = fields.Many2many(comodel_name="ir.attachment",string='Fichiers')

    folder_id = fields.Many2one(comodel_name='flexi.document.folder', string="Dossier",
                                  tracking=True, ondelete='restrict', required=True)

    year_id = fields.Many2one(comodel_name='flexi.document.year', string="Année",
                                tracking=True, ondelete='restrict', required=True)

    month_id = fields.Many2one(comodel_name='flexi.document.month', string="Mois",
                              tracking=True, ondelete='restrict', required=True)

    location_id = fields.Many2one(comodel_name='flexi.document.location', string="Emplacement d'archive",
                               tracking=True, ondelete='restrict', required=False)

    notes = fields.Text(string="Notes additionnelles", tracking=True)

    emission_date = fields.Date(string="Date d'emission", tracking=True)

    expiration_date = fields.Date(string="Date d'emission", tracking=True)

    expiry_notify_delay  = fields.Integer(string="Delai de notification d'expiration (en jours)",
                                          tracking=True, help="Nombre de jours en amont de la "
                                                              "date d'expiration à partir duquel il "
                                                              "faut déjà alerter de l'expiration "
                                                              "prochaine du document")

    auto_archive_if_expired = fields.Boolean(string="Archiver automatiquement quand expiré",
                                             default=lambda self: self.env.user.company_id.archive_expired_documents,
                                             tracking=True)

    notification_date = fields.Date(string="Date de début de notification d'expiration",
                                    compute="_compute_notification_date", store=True)

    is_expired = fields.Boolean(string="Est expiré", tracking=True, store=True,
                                compute="_compute_is_expired")

    active = fields.Boolean(string="Actif", tracking=True, default=True)

    max_expiry_notification = fields.Integer(string="Nombre max de notification d'expiration",
                                             tracking=True)

    total_expiry_notification = fields.Integer(string="Nombre de notification d'expiration effectué",
                                             tracking=True, default=0, readonly=True)

    is_notification_closed = fields.Boolean(string="Notification d'expiration cloturé",
                                            tracking=True, compute="_compute_is_notification_closed",
                                            store=True)

    expiry_user_ids = fields.Many2many(comodel_name="res.users", string="Utilisateurs à notifier",
                                       relation="expiry_user_ids_rel")

    company_id = fields.Many2one(comodel_name='res.company', string="Société",
                                 tracking=True, ondelete='restrict',
                                 default=lambda self: self.env.user.company_id.id)

    @api.depends('notification_date','expiration_date','max_expiry_notification','total_expiry_notification')
    def _compute_is_notification_closed(self):
        for rec in self:
            if rec.notification_date and rec.expiration_date and rec.max_expiry_notification and rec.total_expiry_notification:
                if rec.total_expiry_notification >= rec.max_expiry_notification:
                    rec.is_notification_closed = True
                else: rec.is_notification_closed = False
            else:
                rec.is_notification_closed = False

    @api.onchange('expiration_date')
    def onchange_expiration_date(self):
        if self.expiration_date:
            self.max_expiry_notification = self.env.user.company_id.max_expiry_notification
        else:
            self.max_expiry_notification = False

    @api.constrains('expiry_notify_delay')
    def _check_expiry_notify_delay(self):
        for rec in self:
            if rec.expiry_notify_delay < 1:
                raise ValidationError(_("Le delai de notification d'expiration doit être strictement positif"))

    @api.constrains('max_expiry_notification','expiration_date', 'expiry_user_ids')
    def _check_max_expiry_notification(self):
        for rec in self:
            if rec.expiration_date and not rec.max_expiry_notification:
                raise ValidationError(_("Si vous indiquer une date d'expiration, vous devez aussi indiquer "
                                        "le nombre max de notification d'expiration"))

            if not rec.expiration_date and rec.max_expiry_notification:
                raise ValidationError(_("Vous ne pouvez pas indiquer le nombre max de notification "
                                        "d'expiration sans indiquer de date d'expiration "))

            if rec.max_expiry_notification < 1:
                raise ValidationError(_("Le nombre max de notification d'expiration doit être strictement "
                                        "positif"))

            if rec.expiration_date and not rec.expiry_user_ids:
                raise ValidationError(_("En indiquant une date d'expiration vous devez aussi indiquer "
                                        "au moins 1 utilisateurs à notifier"))

            if not rec.expiration_date and rec.expiry_user_ids:
                raise ValidationError(_("Vous ne pouvez pas indiquer des utilisateurs à notifier en cas "
                                        "d'expiration sans indiquer de date d'expiration"))

    @api.model
    def document_expiration_management(self):
        docs_to_notify = self.env['flexi.document.content'].sudo().\
            search([('notification_date','!=', False),
                    ('notification_date', '>=', datetime.datetime.now().date()),
                    ('is_notification_closed','=',False)
                    ])

        docs_to_archive = self.env['flexi.document.content'].sudo(). \
            search([('is_expired', '=', True),
                    ('active','=',True),
                    ])
        alert_mail_template = self.env.ref('flexi_documents.alert_expiration_document_mail_template')
        archive_mail_template = self.env.ref('flexi_documents.archive_documents_mail_template')

        for doc_notif in docs_to_notify:
            receivers = ",".join(doc_notif.expiry_user_ids.mapped('email_formatted'))
            alert_mail_template.with_context(mails_to=receivers).send_mail(doc_notif.id, force_send=True)
            doc_notif.write({'total_expiry_notification': doc_notif.total_expiry_notification + 1})

        for doc_archive in docs_to_archive:
            receivers = ",".join(doc_archive.expiry_user_ids.mapped('email_formatted'))
            archive_mail_template.with_context(mails_to=receivers).send_mail(doc_archive.id, force_send=True)
            doc_archive.write({'active': False})


    @api.depends('expiration_date', 'expiry_notify_delay')
    def _compute_notification_date(self):
        for rec in self:
            if rec.expiration_date and rec.expiry_notify_delay:
                rec.notification_date = rec.expiration_date - datetime.timedelta(days=rec.expiry_notify_delay)
            else:
                rec.notification_date = False

    @api.depends('expiration_date')
    def _compute_is_expired(self):
        for rec in self:
            if rec.expiration_date and datetime.datetime.now().date() > rec.expiration_date:
                rec.is_expired = True
            else:
                rec.is_expired = False

    @api.constrains('emission_date','expiration_date')
    def _check_document_date(self):
        for rec in self:
            if rec.emission_date and rec.expiration_date:
                if rec.expiration_date <= rec.emission_date:
                    raise ValidationError(_("La date d'expiration doit être supérieur à la date d'emission"))
            if rec.expiration_date and (not rec.expiry_notify_delay or rec.expiry_notify_delay <=0):
                raise ValidationError(_("Vous devez indiquer un delai de notification d'expiration du document"))

    @api.constrains('visibility_type','selected_user_ids', 'selected_profile_ids')
    def _check_visibility_type(self):
        for rec in self:
            if rec.visibility_type == "selected_users" and not rec.selected_user_ids:
                raise ValidationError(_('Vous devez choisir au moins un utilisateur'))
            elif rec.visibility_type != "selected_users" and rec.selected_user_ids:
                raise ValidationError(_('Veuillez vider la liste des utilisateurs sélectionnés précédemment'))

            if rec.visibility_type == "selected_profiles" and not rec.selected_profile_ids:
                raise ValidationError(_("Vous devez choisir au moins un profil d'utilisateur"))
            elif rec.visibility_type != "selected_profiles" and rec.selected_profile_ids:
                raise ValidationError(_('Veuillez vider la liste des profils utilisateurs sélectionnés précédemment'))

    def _compute_visibility_user_ids(self):
        self.ensure_one()
        v_users = self.env['res.users']
        v_users |= self.create_uid #by default the creator of the document should view it
        if self.visibility_type == "all_users":
            v_users |= self.env['res.users'].sudo().search([])
        elif self.visibility_type == "selected_users":
            v_users |= self.selected_user_ids
        elif self.visibility_type == "selected_profiles":
            if self.company_id.document_profile_heritage == "current":
                v_users |= self.selected_profile_ids.user_ids
            elif self.company_id.document_profile_heritage == "hierarchy":
                v_users |= self.selected_profile_ids.get_complete_user_ids()

        self.write({'visibility_user_ids': [(6, 0, v_users.ids)]})

    @api.model_create_multi
    def create(self, vals_list):
        result = super(FlexiDocumentContent, self).create(vals_list)
        for rec in result:
            rec.with_context(create_document_content=True)._compute_visibility_user_ids()
        return result

    def write(self, vals):

        result =  super(FlexiDocumentContent, self).write(vals)
        if not self.env.context.get('create_document_content', False):
            for rec in self:
                    rec._compute_visibility_user_ids()
        return result

    def unlink(self):

        return super(FlexiDocumentContent, self).unlink()
