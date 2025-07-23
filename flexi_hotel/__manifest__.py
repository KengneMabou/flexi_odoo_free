# -*- coding: utf-8 -*-
{

    'name': "Flexible hotel management",
    'summary': """Hotel management for humans: Create better and flexible hotel management solution""",
    'author': "Marex Sarl",
    'version': '17.0.0.1.0',
    'sequence': 30,
    'website': 'marex-sarl.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'hotel_management_odoo','sale', 'sales_team', 'web_domain_field', 'uom'],
    #'external_dependencies':{'python':['email-validator']},
     'data': [
         'security/ir.model.access.csv',
         'views/hotel_room.xml',
         'views/room_booking.xml',
         'views/room_category.xml',
         'views/room_pricing.xml',
         'views/room_pricing_line.xml',
         'views/room_provision.xml',
     ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

