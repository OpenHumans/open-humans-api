from unittest import TestCase
from unittest.mock import mock_open, patch
import arrow
import os
import vcr
from posix import stat_result
import stat
from io import StringIO
from ohapi.utils_fs import (guess_tags, load_metadata_csv,
                            validate_metadata, characterize_local_files,
                            read_id_list, download_file,
                            write_metadata_to_filestream)
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

    """
    Tests for :func:`utils_fs<ohapi.utils_fs>`
    """
    def setUp(self):
        pass

    def test_guess_tags(self):
        """
        Tests for :func:`guess_tags<ohapi.utils_fs.guess_tags>`

        """
        fname = "foo.vcf"
        self.assertEqual(guess_tags(fname), ['vcf'])
        fname = "foo.json.gz"
        self.assertEqual(guess_tags(fname), ['json'])
        fname = "foo.csv.bz2"
        self.assertEqual(guess_tags(fname), ['csv'])

    def test_load_metadata_csv(self):
        """
        Tests for :func:`load_metadata_csv<ohapi.utils_fs.load_metadata_csv>`

        """
        metadata_users = load_metadata_csv('ohapi/tests/data/'
                                           'metadata_proj_member_key.csv')
        self.assertEqual(len(metadata_users.keys()), 2)
        for key in metadata_users:
            self.assertEqual(len(metadata_users[key]), 2)

        metadata_files = load_metadata_csv('ohapi/tests/data/'
                                           'metadata_proj_file_key_works.csv')
        self.assertEqual(len(metadata_files.keys()), 2)

    def test_validate_metadata(self):
        """
        Tests for :func:`validate_metadata<ohapi.utils_fs.validate_metadata>`

        """
        directory = 'ohapi/tests/data/test_directory/'
        metadata = {'file_1.json', 'file_2.json'}
        self.assertEqual(validate_metadata(directory, metadata), True)

    def test_read_id_list_filepath_not_given(self):
        """
        Tests for :func:`read_id_list<ohapi.utils_fs.read_id_list>`

        """
        response = read_id_list(filepath=None)
        self.assertEqual(response, None)

    def test_read_id_list_filepath_given(self):
        """
        Tests for :func:`read_id_list<ohapi.utils_fs.read_id_list>`

        """
        filename = 'sample.txt'
        filedir = 'ohapi/tests/data/test_id_dir/'
        FILEPATH = os.path.join(filedir, filename)
        response = read_id_list(filepath=FILEPATH)
        self.assertEqual(response, ['12345678'])

    @my_vcr.use_cassette()
    def test_download_file_valid_url(self):
        """
        Tests for :func:`download_file<ohapi.utils_fs.download_file>`

        """
        with patch('ohapi.utils_fs.open', mock_open(), create=True):
            FILEPATH = 'ohapi/tests/data/test_download_dir/test_download_file'
            DOWNLOAD_URL = 'http://www.loremipsum.de/downloads/version1.txt'
            response = download_file(
                download_url=DOWNLOAD_URL, target_filepath=FILEPATH)
            self.assertEqual(response.status_code, 200)

    def test_mk_metadata_empty_directory(self):
        with patch('ohapi.utils_fs.os.path.isdir') as mocked_isdir, \
                patch('ohapi.utils_fs.os.listdir') as mocked_listdir:
                mocked_isdir.return_value = True
                mocked_listdir.return_value = []
                teststream = StringIO()
                write_metadata_to_filestream('test_dir', teststream)
                assert(teststream.getvalue() == 'filename,tags,description,' +
                       'md5,creation_date\r\n')

    def test_mk_metadata_single_user(self):
            with patch('ohapi.utils_fs.os.path.isdir') as mocked_isdir, \
                    patch('ohapi.utils_fs.os.listdir') as mocked_listdir:
                with patch('ohapi.utils_fs.open',
                           mock_open(read_data=b'some stuff'),
                           create=True):
                    mocked_isdir.return_value = True
                    mocked_listdir.return_value = ['f1.txt', 'f2.txt']
                    mocked_isdir.side_effect = [False, False]
                    try:
                        def fake_stat(arg):
                            faked = list(orig_os_stat('/tmp'))
                            faked[stat.ST_SIZE] = len("some stuff")
                            faked[stat.ST_CTIME] = "1497164239.6941652"
                            return stat_result(faked)
                        orig_os_stat = os.stat
                        os.stat = fake_stat
                        teststream = StringIO()
                        write_metadata_to_filestream('test_dir', teststream)
                        content = teststream.getvalue()
                        assert(len(content) == 197 and content.startswith(
                            'filename,tags,description,md5,' +
                            'creation_date\r\n') and "f1.txt,,,beb6a43adfb95" +
                            "0ec6f82ceed19beee21,2017-06-11T06:57:19.694165+" +
                            "00:00\r\n" in content and "f2.txt,,,beb6a43adfb" +
                            "950ec6f82ceed19beee21," +
                            "2017-06-11T06:57:19.694165+00:00\r\n" in content)
                    finally:
                        os.stat = orig_os_stat

    def test_mk_metadata_multi_user(self):
        with patch('ohapi.utils_fs.open', mock_open(read_data=b'some stuff'),
                   create=True):
            orig_os_stat = os.stat
            orig_os_is_dir = os.path.isdir
            orig_os_list_dir = os.listdir
            try:
                def fake_stat(arg):
                    faked = list(orig_os_stat('/tmp'))
                    faked[stat.ST_SIZE] = len("some stuff")
                    faked[stat.ST_CTIME] = "1497164239.6941652"
                    return stat_result(faked)

                def fake_list_dir(arg):
                    if arg == 'test_dir':
                        return ['12345678']
                    elif '12345678' in arg:
                        return ['f1.txt', 'f2.txt']

                def fake_is_dir(arg):
                    if ('test_dir') in arg or ('12345678') in arg:
                        return True
                    elif ('f1.txt') in arg or ('f2.txt') in arg:
                        return False
                os.listdir = fake_list_dir
                os.path.isdir = fake_is_dir
                os.stat = fake_stat
                teststream = StringIO()
                write_metadata_to_filestream('test_dir', teststream)
                content = teststream.getvalue()
                assert(len(content) == 233 and content.startswith(
                    'project_member_id,filename,tags,description,md5,' +
                    'creation_date\r\n') and "12345678,f1.txt,,,beb6a43adfb9" +
                    "50ec6f82ceed19beee21,2017-06-11T06:57:19.694165+" +
                    "00:00\r\n" in content and "12345678,f2.txt,,,beb6a43adf" +
                    "b950ec6f82ceed19beee21," +
                    "2017-06-11T06:57:19.694165+00:00\r\n" in content)
            finally:
                os.stat = orig_os_stat
                os.listdir = orig_os_list_dir
                os.path.isdir = orig_os_is_dir
