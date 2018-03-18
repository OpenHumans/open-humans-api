from unittest import TestCase
from ohapi.projects import OHProject

parameter_defaults = {
    'MEMBER_DATA': {"data": [{"basename": 1}]},
    'TARGET_MEMBER_DIR': 'targetmemberdir',
    'MAX_SIZE': 'max_size',
}

"""
_config_params_api.py is not usually present.  You can create this to use valid
codes and tokens if you wish to record new cassettes. If present, this file is
used to overwrite `parameter_defaults` with the (hopefully valid, but secret)
items in the file. DO NOT COMMIT IT TO GIT!

To get started, do:
cp _config_params_api.py.example _config_params_api.py

Edit _config_params_api.py to define valid secret codes, tokens, etc.

Run a specific function to (re)create an associated cassette, e.g.:
pytest ohapi/tests/test_projects.py::ProjectsTest::test_get_member_file_data_member_data_none

(This only makes a new cassette if one doesn't already exist!)
"""
try:
    from _config_params_api import params
    for param in params:
        parameter_defaults[param] = params[param]
except ImportError:
    pass

for param in parameter_defaults:
    locals()[param] = parameter_defaults[param]


class ProjectsTest(TestCase):

    def setUp(self):
        pass

    def test_get_member_file_data_member_data_none(self):
        response = OHProject._get_member_file_data(member_data=MEMBER_DATA)
        self.assertEqual(response, {1: {'basename': 1}})
