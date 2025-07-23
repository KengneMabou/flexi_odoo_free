# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class RoomCategory(models.Model):

    _name = "room.category"
    _description = "Room category"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        return self.env.user.company_id.id

    name = fields.Char(string="Name", required=True, tracking=True)

    company_id = fields.Many2one(string='Société', comodel_name="res.company", default=_default_company,
                                 index=True, required=True, tracking=True, ondelete='restrict',
                                 copy=False, readonly=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
