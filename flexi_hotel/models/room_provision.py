# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class RoomProvision(models.Model):
   
    _name = "room.provision"
    _description = "Room accommodation provision (nap, half day, overnight, etc)"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        return self.env.user.company_id.id

    name = fields.Char(string="Name", required=True, tracking=True)

    min_duration = fields.Float(string='Min duration (minutes)',
                                required=True, tracking=True,
                                help="Min duration (in hours) at which customer enter this room provision")

    max_duration = fields.Float(string='Max duration (minutes)',
                                  required=False, tracking=True,
                                  help="Max duration in hours at which customer exit from this room provision",)

    uom_id = fields.Many2one(comodel_name='uom.uom', string="Unit of Measure",
                             help="This will set the unit of measure used",
                             required=True, ondelete="restrict", tracking=True,)

    category_id = fields.Many2one(comodel_name='room.category', string="Room category",
                                 required=True, ondelete="restrict", tracking=True, )

    company_id = fields.Many2one(string='Société', comodel_name="res.company", default=_default_company,
                                 index=True, required=True, tracking=True, ondelete='restrict',
                                 copy=False, readonly=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    @api.model
    def get_room_provision_id(self, booking_duration, room_category):
        self.ensure_one()
        all_provision = self.env['room.provision'].search([('category_id', '=', room_category.id),
                                                           ], order="min_duration asc")

        intervals_lst = self.get_provision_intervals(all_provision)

        for item in intervals_lst:
            if item[0] == 0 and booking_duration == 0:
                return item[2]

            if not item[1] and booking_duration > item[0]:
                return item[2]

            if item[0] < booking_duration < item[1]:
                return item[2]

            if item[1] == booking_duration :
                return item[2]

        return False

    @api.model
    def get_provision_intervals(self, all_provision):
        intervals_lst = list()
        for prov in all_provision:
            intervals_lst.append((prov.min_duration if prov.min_duration else 0,
                                  prov.max_duration if prov.max_duration else False, prov.id))

        return intervals_lst

    @api.constrains('category_id','min_duration', 'max_duration')
    def _check_duration_intervals(self):
        for rec in self:
            all_provision = self.env['room.provision'].search([('category_id', '=', rec.category_id.id),
                                                               ], order="min_duration asc")

            intervals_lst = self.get_provision_intervals(all_provision)
            for k in range(len(intervals_lst)):
                if k == 0 and intervals_lst[k][0] != 0:
                    # we check the first item of first provision interval that should be zero
                    raise ValidationError(_("The first item of first provision interval that should be zero"))

                if k == (len(intervals_lst) - 1) and intervals_lst[k][1] != False:
                    raise ValidationError(_("The last item of last provision interval should not be set"))

                if intervals_lst[k][1] != intervals_lst[k+1][0] and len(intervals_lst) > 1:
                    raise ValidationError(_("The last item of last provision interval should not be set"))

    @api.constrains('uom_id','category_id')
    def _check_provision_duplication(self):
        for rec in self:
            all_provision  = self.env['room.provision'].search([('uom_id','=',rec.uom_id.id),
                                                                ('category_id','=',rec.category_id.id),
                                                                ])
            if len(all_provision) > 1:
                raise ValidationError(_("02 room's provision cannot be linked to "
                                        "the same unit of mesure and room category"))

    @api.constrains("min_duration", "max_duration")
    def _check_max_duration_values(self):
        """Check max duration"""
        for rec in self:
            if rec.max_duration <= 0:
                raise ValidationError(_("Room provision's max duration must be "
                                        "more than 0 or not set"))

            if rec.min_duration <= 0:
                raise ValidationError(_("Room provision's min duration must be more than 0"))

            if rec.max_duration and rec.max_duration < rec.min_duration:
                raise ValidationError(_("if set, room provision's max duration must "
                                        "be greater or equal than min duration "))
