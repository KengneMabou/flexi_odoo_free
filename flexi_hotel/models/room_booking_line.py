# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import logging
import datetime
from math import ceil
_logger = logging.getLogger(__name__)


class RoomBookingLine(models.Model):

    _inherit = 'room.booking.line'

    room_amenities_ids = fields.Many2many(related="booking_id.room_amenities_ids")

    room_type = fields.Selection(related="booking_id.room_type")

    floor_id = fields.Many2one(related="booking_id.floor_id")

    room_id = fields.Many2one(domain="[('id','in',room_domain)]")

    room_domain = fields.Json(string="Room selection domain", compute="_compute_room_domain")

    price_unit = fields.Float(related='provision_unit_price',)

    provision_unit_price = fields.Float(compute="_compute_provision_unit_price")

    occupant_ids = fields.Many2many(string="Occupants", comodel_name="res.partner",
                                    tracking=True)

    provision_id = fields.Many2one(comodel_name='room.provision', string="Room booking provision",
                                   required=False, ondelete="restrict", tracking=True, store=True,
                                   readonly=True, compute="_compute_booking_provision")

    # is_overnight = fields.Boolean(string="Is overnight ?", compute='_compute_booking_period')
    #
    # is_half_day = fields.Boolean(string="Is half day ?", compute='_compute_booking_period')
    #
    # is_nap = fields.Boolean(string="Is nap ?", compute='_compute_booking_period')

    booking_duration = fields.Integer(string="Booking duration in minutes",
                                      compute="_compute_booking_duration")

    in_reservation = fields.Boolean(related='booking_id.in_reservation')

    @api.depends('room_type', 'room_amenities_ids','floor_id')
    def _compute_room_domain(self):
        for rec in self:
            room_filer = []
            if rec.room_amenities_ids:
                room_filer.append(('room_amenities_ids','in',rec.room_amenities_ids.ids))
            if rec.floor_id:
                room_filer.append(('floor_id','=',rec.floor_id.id))
            if rec.room_type:
                room_filer.append(('room_type', '=', rec.room_type))

            selected_rooms = self.env['hotel.room'].search(room_filer)
            if not selected_rooms:
                selected_rooms = self.env['hotel.room'].search([])

            rec.room_domain = selected_rooms.ids

    @api.depends('provision_id','room_id')
    def _compute_provision_unit_price(self):
        for rec in self:
            if rec.provision_id:
                price_line = rec.room_id.pricing_id.pricing_line_ids.\
                    filtered(lambda pl: pl.provision_id.id == rec.provision_id.id)
                if len(price_line) == 1:
                    rec.provision_unit_price = price_line.amount
                else:
                    rec.provision_unit_price = 0
            else:
                rec.provision_unit_price = 0

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):
        result = super(RoomBookingLine, self)._onchange_checkin_date()
        self.uom_qty = self.get_hotel_booking_real_qty()
        return result

    def get_hotel_booking_real_qty(self):
        self.ensure_one()
        qty = 1
        diffdate = None
        if self.checkin_date and self.checkout_date and (
                self.state == "check_out" or self.checkin_date > datetime.datetime.now()):
            diffdate = self.checkout_date - self.checkin_date
        elif self.checkin_date:
            diffdate = datetime.datetime.now() - self.checkin_date

        if diffdate and diffdate.days >= 1:
            qty = round(diffdate.total_seconds() / 86400, 2)

        return qty

    @api.onchange('provision_id')
    def onchange_provision_id(self):
        self.uom_id = self.provision_id.uom_id.id

    @api.depends('checkin_date', 'checkout_date')
    def _compute_booking_duration(self):
        for rec in self:
            rec.booking_duration = ceil((rec.checkout_date - rec.checkin_date).total_seconds() / 60)

    @api.depends('booking_duration')
    def _compute_booking_provision(self):
        for rec in self:
            rec.provision_id = self.env['room.provision'].get_room_provision_id(rec.booking_duration,
                                                                                rec.room_id.category_id)
    # @api.constrains('booking_id')
    def _check_one_booking_line(self):
        """Check that that booking has one booking line"""
        for rec in self:
            tot_line = self.env['room.booking.line'].search_count([('booking_id','=',rec.booking_id.id)])
            if tot_line > 1:
                raise ValidationError(_("The booking folio should have only one booking line"))

    @api.constrains('room_id', 'occupant_ids')
    def _check_occupant_ids(self):
        """Check occupants for overnigth booking"""
        for rec in self:
            if rec.is_overnight and not rec.occupant_ids:
                raise ValidationError(_("For overnight, you should proved at least one occupant"))

    @api.constrains('room_id', 'occupant_ids')
    def _check_booking_occupancy(self):
        """"Check occupants for room capacity"""
        for rec in self:
            if len(rec.occupant_ids) > rec.room_id.num_person:
                raise ValidationError(_("The number of occupant in the booking line cannot "
                                        "be greater than the "))