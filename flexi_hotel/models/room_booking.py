# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)


class RoomBooking(models.Model):

    _inherit = 'room.booking'

    in_reservation = fields.Boolean(compute='_compute_in_reservation',store=True)

    room_amenities_ids = fields.Many2many(comodel_name="hotel.amenity", string="Room Amenities",
                                          help="Select room amenities preferences.")

    room_type = fields.Selection(selection=[('single', 'Single'),
                                            ('double', 'Double'),
                                            ('dormitory', 'Dormitory')],
                                 string="Room Type", help="Selects the Room Type preference",tracking=True,)

    floor_id = fields.Many2one(comodel_name='hotel.floor', string='Floor', help="Selects the floor preference",
                               tracking=True)

    @api.constrains('partner_id','room_line_ids')
    def _check_booking_lines(self):
        for rec in self:
            if len(rec.room_line_ids) != 1:
                raise ValidationError(_("The booking folio should have one booking line"))

    @api.depends("state")
    def _compute_in_reservation(self):
        for rec in self:
            if rec.state in ['draft','reserved']:
                rec.in_reservation = True
            else:
                rec.in_reservation = False

    def action_reserve(self):
        self.room_line_ids._check_occupant_ids()
        return super(RoomBooking, self).action_reserve()

    def action_checkin(self):
        self.room_line_ids._check_occupant_ids()
        result = super(RoomBooking, self).action_checkin()
        self.room_line_ids.write({'checkin_date': datetime.datetime.now()})
        return result
    
    def action_checkout(self):
        self.room_line_ids._check_occupant_ids()
        result = super(RoomBooking, self).action_checkout()
        self.room_line_ids.write({'checkout_date': datetime.datetime.now()})
        return  result

    def action_done(self):
        """Rewrite of Button action_confirm function"""
        self.room_line_ids._check_occupant_ids()
        booking_invoices = self.env['account.move'].search([('ref', '=', self.name)])
        tot_residual = sum(booking_invoices.mapped('amount_residual'))
        if tot_residual == 0:
            self.write({"state": "done"})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Booking Checked Out Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            raise ValidationError(_('Some invoices related to this hotel booking are still due for Payment.'))