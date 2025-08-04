# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):

    _inherit = 'res.users'

    nextcloud_url = fields.Char(string="Nextcloud url", tracking=True,
                         help="Nextcloud http url like https://example.com")

    nextcloud_login = fields.Char(string="Nextcloud login", tracking=True)

    nextcloud_passwd = fields.Char(string="Nextcloud password", tracking=True)

