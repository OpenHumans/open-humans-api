from unittest import TestCase
from unittest.mock import mock_open, patch
import arrow
import os
import vcr

from ohapi.utils_fs import (guess_tags, load_metadata_csv,
                            validate_metadata, characterize_local_files,
                            read_id_list, download_file)
from humanfriendly import parse_size

MAX_FILE_DEFAULT = parse_size('128m')

parameter_defaults = {
    'CLIENT_ID_VALID': 'validclientid',
    'CLIENT_SECRET_VALID': 'validclientsecret',
    'CODE_VALID': 'validcode',
    'REFRESH_TOKEN_VALID': 'validrefreshtoken',
    'CLIENT_ID_INVALID': 'invalidclientid',
    'CLIENT_SECRET_INVALID': 'invalidclientsecret',
    'CODE_INVALID': 'invalidcode',
    'REFRESH_TOKEN_INVALID': 'invalidrefreshtoken',
    'REDIRECT_URI': 'http://127.0.0.1:5000/authorize_openhumans/',
    'ACCESS_TOKEN': 'accesstoken',
    'ACCESS_TOKEN_EXPIRED': 'accesstokenexpired',
    'ACCESS_TOKEN_INVALID': 'accesstokeninvalid',
    'MASTER_ACCESS_TOKEN': 'masteraccesstoken',
    'INVALID_PMI1': 'invalidprojectmemberid1',
    'INVALID_PMI2': 'invalidprojectmemberid2',
    'VALID_PMI1': 'validprojectmemberid1',
    'VALID_PMI2': 'validprojectmemberid2',
    'SUBJECT': 'testsubject',
    'MESSAGE': 'testmessage',

}

try:
    from _config_params_api import params
    for param in params:
        parameter_defaults[param] = params[param]
except ImportError:
    pass

for param in parameter_defaults:
    locals()[param] = parameter_defaults[param]


FILTERSET = [('access_token', 'ACCESSTOKEN'), ('client_id', 'CLIENTID'),
             ('client_secret', 'CLIENTSECRET'), ('code', 'CODE'),
             ('refresh_token', 'REFRESHTOKEN'),
             ('invalid_access_token', 'INVALIDACCESSTOKEN')]

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes',
                 filter_headers=[('Authorization', 'XXXXXXXX')],
                 filter_query_parameters=FILTERSET,
                 filter_post_data_parameters=FILTERSET)


def test_test():
    x = 1 + 2
    assert x == 3


class UtilsTest(TestCase):

    def setUp(self):
        pass

    def test_guess_tags(self):
        fname = "foo.vcf"
        self.assertEqual(guess_tags(fname), ['vcf'])
        fname = "foo.json.gz"
        self.assertEqual(guess_tags(fname), ['json'])
        fname = "foo.csv.bz2"
        self.assertEqual(guess_tags(fname), ['csv'])

    def test_load_metadata_csv(self):
        metadata_users = load_metadata_csv('ohapi/tests/data/'
                                           'metadata_proj_member_key.csv')
        self.assertEqual(len(metadata_users.keys()), 2)
        for key in metadata_users:
            self.assertEqual(len(metadata_users[key]), 2)

        metadata_files = load_metadata_csv('ohapi/tests/data/'
                                           'metadata_proj_file_key_works.csv')
        self.assertEqual(len(metadata_files.keys()), 2)

    def test_validate_metadata(self):
        directory = 'ohapi/tests/data/test_directory/'
        metadata = {'file_1.json', 'file_2.json'}
        self.assertEqual(validate_metadata(directory, metadata), True)

    def test_read_id_list_filepath_not_given(self):
        response = read_id_list(filepath=None)
        self.assertEqual(response, None)

    def test_read_id_list_filepath_given(self):
        filename = 'sample.txt'
        filedir = 'ohapi/tests/data/test_id_dir/'
        FILEPATH = os.path.join(filedir, filename)
        response = read_id_list(filepath=FILEPATH)
        self.assertEqual(response, ['12345678'])

    @my_vcr.use_cassette()
    def test_download_file_valid_url(self):
        with patch('ohapi.utils_fs.open', mock_open(), create=True):
            FILEPATH = 'ohapi/tests/data/test_download_dir/test_download_file'
            DOWNLOAD_URL = 'http://www.loremipsum.de/downloads/version1.txt'
            response = download_file(
                download_url=DOWNLOAD_URL, target_filepath=FILEPATH)
            self.assertEqual(response.status_code, 200)
