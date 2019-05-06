# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class TestHrAttendanceExtend(TransactionCase):


    def test_itis_holiday_create(self):
        """test case to test creation of the hr holidays"""

        itis_holiday = self.env['itis.holiday']
        today_date = datetime.now().date().strftime('%Y-%m-%d')
        itis_holiday_rec = itis_holiday.create({'name':'Holiday','date':today_date})
        if itis_holiday_rec:
            _logger.info('-----Holiday is successfully created.')
        else:
            self.assertEqual(0,1,'Odoo-Alfresco:- Holiday test case is failed.')


