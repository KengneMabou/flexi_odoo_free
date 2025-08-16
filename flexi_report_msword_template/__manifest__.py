# -*- coding: utf-8 -*-
{
    'name': "Docx reporting",
    'description': "Report made using MS word based templates (doc, docx)",
    'website': 'marex-sarl.com',
    'category': 'Tools',
    'author': "Marex sarl & Kengne Mabou",
    'version': '17.0.1.0..0',
    'depends': ['base'],
    'data': [
        'views/ir_actions_report_views.xml',
        'views/res_company.xml',
    ],
    'external_dependencies':{'python':['docxtpl',
                                       'python-docx',
                                       #'docx-mailmerge',
                                       ]
                             },
    'currency': 'EUR',
    'support':"kmhfmassive@gmail.com",
    'price': 0,
    'license': 'AGPLv3',
}
