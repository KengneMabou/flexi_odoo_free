# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FlexiDocumentYear(models.Model):

    _name = 'flexi.document.year'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Année de document"

    name = fields.Char(string="Intitulé", required=True, tracking=True, )

    company_id = fields.Many2one(comodel_name='res.company', string="Société",
                                 tracking=True, ondelete='restrict',
                                 default=lambda self: self.env.user.company_id.id)

    @api.constrains('name')
    def _check_doc_year_name(self):
        for rec in self:
            try:
                int(rec.name)
            except Exception as e:
                raise ValidationError(_("L'année doit être un entier. Details: %s", e.args[0]))

            prev_records = self.env['flexi.document.year'].search([]).\
                filtered(lambda doc_year: doc_year.name.lower() == rec.name.lower())

            if len(prev_records)  > 1:
                raise ValidationError(_("Deux années ne peuvent pas avoir le nom. Les noms "
                                        "sont insensibles à la casse (Par exemple 'Achats', 'achats' ou "
                                        "'ACHATS' considérés comme équivalentes"))
