# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FlexiDocumentMonth(models.Model):

    _name = 'flexi.document.month'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Dossier de document"

    name = fields.Char(string="Nom", required=True, tracking=True, translate=True)

    company_id = fields.Many2one(comodel_name='res.company', string="Société",
                                 tracking=True, ondelete='restrict',
                                 default=lambda self: self.env.user.company_id.id)

    @api.constrains('name')
    def _check_doc_month_name(self):
        for rec in self:
            prev_records = self.env['flexi.document.month'].search([]).\
                filtered(lambda doc_month: doc_month.name.lower() == rec.name.lower())

            if len(prev_records) > 1:
                raise ValidationError(_("Deux dossiers ne peuvent pas avoir le nom. Les noms "
                                        "sont insensibles à la casse (Par exemple 'Achats', 'achats' ou "
                                        "'ACHATS' considérés comme équivalentes"))
