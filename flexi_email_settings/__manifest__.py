# -*- coding: utf-8 -*-

{
    'name': 'Email account settings',
    'summary': 'Self-service email account settings',
    'version': '17.0.1.0.0',
    'license': 'OPL-1',
    'support': 'contact@marex-sarl.com',
    'category': 'Tools',
    "sequence": 3,
    'price': 00.00,
    'currency': 'EUR',
    'author': 'Marex Sarl & Kengne Mabou Herve',
    'website': 'marex-sarl.com',
    'depends': ['base','mail'],
    'data': [
        'views/menu.xml',
        'views/incoming_mailserver.xml',
        'views/outgoing_mailserver.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
