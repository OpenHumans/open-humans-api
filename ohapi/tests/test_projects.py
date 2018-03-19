from unittest import TestCase
from ohapi.projects import OHProject
import vcr

parameter_defaults = {
    'MEMBER_DATA': {"data": [{"basename": 1}]},
    'TARGET_MEMBER_DIR': 'targetmemberdir',
    'MAX_SIZE': 'max_size',
    'MASTER_ACCESS_TOKEN': 'masteraccesstoken',
    'MASTER_ACCESS_TOKEN_EXPIRED': 'masteraccesstokenexpired',
    'MASTER_ACCESS_TOKEN_INVALID': 'masteraccesstokeninvalid',
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


FILTERSET = [('access_token', 'ACCESSTOKEN')]

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes',
                 filter_headers=[('Authorization', 'XXXXXXXX')],
                 filter_query_parameters=FILTERSET,
                 filter_post_data_parameters=FILTERSET)


class ProjectsTest(TestCase):

    def setUp(self):
        pass

    def test_get_member_file_data_member_data_none(self):
        response = OHProject._get_member_file_data(member_data=MEMBER_DATA)
        self.assertEqual(response, {1: {'basename': 1}})


class ProjectsTestUpdateData(TestCase):

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_update_data_valid_master_access_token(self):
        ohproject = OHProject(master_access_token=MASTER_ACCESS_TOKEN)
        response = ohproject.update_data()
        self.assertEqual(len(response), 3)

    @my_vcr.use_cassette
    def test_update_data_expired_master_access_token(self):
        self.assertRaises(Exception, OHProject, MASTER_ACCESS_TOKEN_EXPIRED)

    @my_vcr.use_cassette
    def test_update_data_invalid_master_access_token(self):
        self.assertRaises(Exception, OHProject, MASTER_ACCESS_TOKEN_INVALID)
