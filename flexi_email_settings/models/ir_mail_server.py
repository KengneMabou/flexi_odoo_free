# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    owner_setting_user_id = fields.Many2one(string="Settings owner", comodel_name="res.users",
                                            default=lambda self: self.env.user)

    is_personal_settings = fields.Boolean(string="Is personal settings ?", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for rec in vals_list:
            rec['is_personal_settings'] = self._context.get('is_personal_settings', False)

        return super().create(vals_list)
