# -*- coding: utf-8 -*-

from odoo import models


class HrPayslip(models.Model):
    """Classe pour gérer les fiches de paie."""
    
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'dms.mixin']

    