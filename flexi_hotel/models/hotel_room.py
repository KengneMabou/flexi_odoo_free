# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class HotelRoom(models.Model):

    _inherit = 'hotel.room'

    pricing_id = fields.Many2one(comodel_name='room.pricing', string="Room pricing",
                                   required=True, ondelete="restrict", tracking=True, )

    category_id = fields.Many2one(comodel_name='room.category', string="Room category",
                                  required=True, ondelete="restrict", tracking=True, )