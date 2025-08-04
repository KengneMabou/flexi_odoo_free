# -*- coding: utf-8 -*-
from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):

    _inherit = 'res.company'

    dms_download_type = fields.Selection(string="dms download type",
                                         selection=[('url','URL'),
                                                    ('binary','Binary'),
                                                    ],
                                         tracking=True, default='url', required=True
                                         )

