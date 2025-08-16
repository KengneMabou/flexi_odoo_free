# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    gotenberg_http_base_url = fields.Char(string="Gotenberg base url",
                                          help="Base http url for accessing Gotenberg service for "
                                               "pdf conversion. Eg: http://127.0.0.1:3000", tracking=True)
