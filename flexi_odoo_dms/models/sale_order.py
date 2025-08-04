# -*- coding: utf-8 -*-

from odoo import models


class SaleOrder(models.Model):
    """Classe pour gérer les ventes."""
    
    _name = 'sale.order'
    _inherit = ['sale.order', 'dms.mixin']


    