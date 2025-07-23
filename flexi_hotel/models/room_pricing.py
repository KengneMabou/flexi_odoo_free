# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class RoomPricing(models.Model):

    _name = "room.pricing"
    _description = "Room pricing"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        return self.env.user.company_id.id

    name = fields.Char(string="Name", required=True, tracking=True)

    pricing_line_ids = fields.One2many(comodel_name="room.pricing.line", inverse_name="pricing_id")

    company_id = fields.Many2one(string='Société', comodel_name="res.company", default=_default_company,
                                 index=True, required=True, tracking=True, ondelete='restrict',
                                 copy=False, readonly=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)