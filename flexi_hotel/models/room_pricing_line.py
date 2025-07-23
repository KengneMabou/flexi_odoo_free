# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class RoomPricingLine(models.Model):

    _name = "room.pricing.line"
    _description = "Room pricing line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        return self.env.user.company_id.id

    amount = fields.Float(string='Amount', required=True, tracking=True,)

    provision_id = fields.Many2one(comodel_name='room.provision', string="Room booking provision",
                                   required=True, ondelete="restrict", tracking=True, )

    pricing_id = fields.Many2one(comodel_name='room.pricing', string="Room pricing",
                                 required=True, ondelete="restrict", tracking=True,)

    company_id = fields.Many2one(string='Société', comodel_name="res.company", default=_default_company,
                                 index=True, required=True, tracking=True, ondelete='restrict',
                                 copy=False, readonly=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    @api.constrains('pricing_id','provision_id')
    def _check_price_line_category(self):
        for rec in self:
            all_lines = self.env['room.pricing.line'].search([('pricing_id', '=', rec.pricing_id.id)])
            if len(all_lines.provision_id.category_id.ids) > 1:
                raise ValidationError(_("Provision of each pricing line should be linked to the same room category"))

    @api.constrains('provision_id')
    def _check_provision_id(self):
        for rec in self:
            tot_line = self.env['room.pricing.line'].search_count([('provision_id', '=', rec.provision_id.id)])
            if tot_line > 1:
                raise ValidationError(_("Each pricing line should be linked to its own provision"))

    @api.constrains("amount")
    def _check_amount(self):
        """Check amount"""
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Room pricing line must be more than 0"))