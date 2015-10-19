import os
import unittest
import hipappear
from hipappear import app
from pymongo import MongoClient


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = hipappear.app
        os.environ['MONGOHQ_URL'] = 'mongodb://localhost:27017/testdb'
        self.client = MongoClient()
        app.config['TESTING'] = True
        app = app.test_client()

    def tearDown(self):
        self.client.drop_database('testdb')
        self.client.disconnect()

    def add_mock_tenant_settings(self):
        with app.test_request_context('/dummy'):
            pass

if __name__ == '__main__':
    unittest.main()
