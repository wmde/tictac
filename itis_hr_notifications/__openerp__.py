# -*- coding: utf-8 -*-
{
    'name': "ITIS HR Notifications",

    'summary': """
        A module by ITIS to send various HR notifications""",

    'description': """
        A module by ITIS to send various HR notifications
    """,

    'author': "ITIS AG",
    'website': "http://itis.de",
    'category': 'Human Resource',
    'version': '1.0.55.0',

    'depends': ['hr', 'itis_hr_attendance_extend', 'itis_hr_extend'],

    'data': [
        'data/email_templates.xml',
        'hr_view.xml',
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
    ],
    
    'application': False,
