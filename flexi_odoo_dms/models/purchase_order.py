# -*- coding: utf-8 -*-

from odoo import models


class PurchaseOder(models.Model):
    """Classe pour gérer les achats."""

    _name = 'purchase.order'
    _inherit = ['purchase.order', 'dms.mixin']


    

   