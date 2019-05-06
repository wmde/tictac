# -*- coding: utf-8 -*-
{
    'name': "ITIS Payroll Export",

    'summary': """
        ITIS Payroll Export
    """,

    'description': """
        Module will export Payroll data to csv file
    """,

    'author': "ITIS AG",
    'website': "http://www.itis.de",

    'category': 'HR',
    'version': '1.0.55.0',

    # any module necessary for this one to work correctly
    'depends': ['itis_hr_leave_extend', 'itis_hr_extend'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'hr_setting_view.xml',
        'wizard/payroll_export.xml',
    ],
