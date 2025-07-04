# -*- coding: utf-8 -*-
from odoo import models, fields, _
from geopy.distance import geodesic, great_circle
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    last_latitude = fields.Float(string="Last latitude", digits=(10, 7), readonly=True)
    last_longitude = fields.Float(string="Last longitude", digits=(10, 7), readonly=True)

    def _attendance_action_change(self, geo_information=None):
        attendance = super()._attendance_action_change(geo_information=geo_information)
        if self._context.get('face_recognition'):
            if not self.company_id.partner_id.partner_latitude and not self.company_id.partner_id.partner_longitude:
                raise ValidationError(_("The company of this employee has no geolocation "
                                        "information on partner attached "))

            if attendance.check_in and not attendance.in_latitude and not attendance.in_longitude:
                raise ValidationError(_("The check in has no geolocation information"))

            if attendance.check_out and not attendance.out_latitude and not attendance.out_longitude:
                raise ValidationError(_("The check out has no geolocation information"))

            # if not attendance.check_out:
            #     attendance.in_latitude = self.last_latitude
            #     attendance.in_longitude = self.last_longitude
            # else:
            #     attendance.out_latitude = self.last_latitude
            #     attendance.out_longitude = self.last_longitude

            employee_position = (attendance.out_latitude, attendance.out_longitude) if (
                attendance.check_out) else (attendance.in_latitude, attendance.in_longitude)

            company_position = (self.company_id.partner_id.partner_latitude, self.company_id.partner_id.partner_longitude)
            gd = geodesic(employee_position, company_position)
            if gd.km > 0.1:
                _logger.error("Attendance by face recognition for %s at %s: %s km", employee_position, company_position, gd.km)
                raise ValidationError(_("Please you should check your presence at the "
                                        "company with a mobile device with a gps chip"))

        return attendance
