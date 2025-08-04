# -*- coding: utf-8 -*-
{
    'name': "Odoo to DMS",
    'description': "Odoo integration with DMS like Nextcloud, Alfresco, Google Drive, etc.",
    "version": "17.0.1.0.0",
    'author': "Marex Sarl",
    'website': 'marex-sarl.com',
    'category': 'Document',
    'depends': ['base','sale','purchase','payroll','account'],
    'external_dependencies':{'python':['nc-py-api'],
                             },
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/hr_payslip_view.xml',
        'views/account_move_view.xml',
        'views/dms_folder_select_view.xml',
        'views/dms_file_confirm_view.xml',
        'views/dms_file_select_view.xml',
        'views/dms_send_attachment_view.xml',
        'views/dms_signature_confirm_view.xml',
        'views/dms_signature_request_view.xml',
        'views/res_company_view.xml',
        'views/res_users_view.xml',
    ],
    
    # data files containing optionally loaded demonstration data
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}