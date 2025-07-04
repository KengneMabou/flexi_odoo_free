# -*- coding: utf-8 -*-
{
    'name': 'Attendance by face recognition',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Make attendance of employees by recognizing their faces""",
    'description': """This module introduces a face recognition system in the 
    attendance module so that employees can check in  and check out after 
    recognizing their faces """,
    'author': 'Kengne Mabou Hervé & Marex Sarl',
    'company': 'Marex Sarl',
    'maintainer': 'Kengne Mabou Hervé',
    'website': "marex-sarl.com",
    'depends': ['base', 'mail', 'hr_attendance','base_geolocalize'],
    'data':['views/hr_employee.xml'],
    'assets': {
        'hr_attendance.assets_public_attendance': [
            'flexi_face_attendance/static/src/js/face-api.min.js',
            'flexi_face_attendance/static/src/xml/face_recognition_template.xml',
            'flexi_face_attendance/static/src/js/face_recognition.js',
        ]
    },
    "external_dependencies":{
        "python": ["geopy"]
    },
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
