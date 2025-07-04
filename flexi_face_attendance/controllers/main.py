# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.hr_attendance.controllers.main import HrAttendance
from odoo import _, http


class HrAttendances(HrAttendance):
    """Controllers Overrides to add the Face detection feature"""

    @http.route('/get_image', type="json",
                auth="public")
    def get_image(self,employee_id):
        image = request.env['hr.employee'].sudo().browse(employee_id).image_1920
        return image

    @http.route('/set_employee_location', type="json",
                auth="public")
    def set_employee_geolocation(self, employee_id, latitude, longitude):
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        employee.write({'last_latitude': latitude, 'last_longitude':longitude})
        return {}

    @http.route('/hr_attendance/manual_selection', type="json", auth="public")
    def manual_selection(self, token, employee_id, pin_code):
        company = self._get_company(token)
        if company:
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if employee.company_id == company and (
                    (not company.attendance_kiosk_use_pin) or (employee.pin == pin_code)):
                employee.with_context(face_recognition=True).sudo()._attendance_action_change(self._get_geoip_response('kiosk',
                                                                                                                       latitude=employee.last_latitude,
                                                                                                                       longitude=employee.last_longitude
                                                                                                                       ))
                return self._get_employee_info_response(employee)
        return {}
