# -*- coding:utf-8 -*-

from odoo import api, fields, models


class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    flexi_document_content_id = fields.Many2one(comodel_name='flexi.document.content',
                                                string="Contenu de document", tracking=True,
                                                ondelete='restrict', required=True)
