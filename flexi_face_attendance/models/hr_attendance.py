# -*- coding: utf-8 -*-
from odoo import models, api, _
from geopy.distance import geodesic
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):

    _inherit = "hr.attendance"

    @api.constrains('check_in','check_out')
    def _check_backoffice_attendance(self):
        for rec in self:
            if not self._context.get('face_recognition') and not self.user_has_groups('hr_attendance.group_hr_attendance_manager'):
                if rec.check_in and not rec.in_latitude and not rec.in_longitude:
                    raise ValidationError(_("Only attendance admin can create attendance without "
                                            "check out geolocation information"))
                if rec.check_out and not rec.out_latitude and not rec.out_longitude:
                    raise ValidationError(_("Only attendance admin can create attendance without "
                                            "check out geolocation information"))