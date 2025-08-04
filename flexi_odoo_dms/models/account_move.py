# -*- coding: utf-8 -*-

from odoo import models


class AccountMove(models.Model):
    """Classe pour gérer les mouvements comptable."""
    
    _name = 'account.move'
    _inherit = ['account.move', 'dms.mixin']

    