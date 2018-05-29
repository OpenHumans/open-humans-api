from unittest import TestCase
from unittest.mock import mock_open, patch, MagicMock
import pytest
import vcr
import os
import stat
from posix import stat_result

from ohapi.api import (
    SettingsError, oauth2_auth_url, oauth2_token_exchange,
    get_page, message, delete_file, upload_file, upload_aws)

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
    'REMOTE_FILE_INFO': {"download_url": "https://valid_url"},
    'FILE_METADATA': 'filemetadata',
    'FILE_METADATA_INVALID': 'file_metadata_invalid',
    'FILE_METADATA_INVALID_WITH_DESC': 'file_metadata_invalid_with_desc',
    'MAX_BYTES': 'maxbytes'
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
pytest ohapi/tests/test_api.py::APITest::test_oauth2_token_exchange__valid_code

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


FILTERSET = [('access_token', 'ACCESSTOKEN'), ('client_id', 'CLIENTID'),
             ('client_secret', 'CLIENTSECRET'), ('code', 'CODE'),
             ('refresh_token', 'REFRESHTOKEN'),
             ('invalid_access_token', 'INVALIDACCESSTOKEN')]

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes',
                 filter_headers=[('Authorization', 'XXXXXXXX')],
                 filter_query_parameters=FILTERSET,
                 filter_post_data_parameters=FILTERSET)


class APITestOAuthTokenExchange(TestCase):
    """
    Tests for :func:`oauth2_auth_url<ohapi.api.oauth2_auth_url>`.
    """

    def setUp(self):
        pass

    def test_oauth2_auth_url__no_client_id(self):
        with pytest.raises(SettingsError):
            oauth2_auth_url()

    def test_oauth2_auth_url__with_client_id(self):
        auth_url = oauth2_auth_url(client_id='abcd1234')
        assert auth_url == (
            'https://www.openhumans.org/direct-sharing/projects/'
            'oauth2/authorize/?client_id=abcd1234&response_type=code')

    def test_oauth2_auth_url__with_client_id_and_redirect_uri(self):
        auth_url = oauth2_auth_url(client_id='abcd1234',
                                   redirect_uri='http://127.0.0.1:5000/auth/')
        assert auth_url == (
            'https://www.openhumans.org/direct-sharing/projects/'
            'oauth2/authorize/?client_id=abcd1234&response_type=code'
            '&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fauth%2F')

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__valid_code(self):
        data = oauth2_token_exchange(
            code=CODE_VALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {
            'access_token': 'returnedaccesstoken',
            'expires_in': 36000,
            'refresh_token': 'returnedrefreshtoken',
            'scope': 'american-gut read wildlife open-humans write '
                     'pgp go-viral',
            'token_type': 'Bearer'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_code(self):
        with self.assertRaises(Exception):
            data = oauth2_token_exchange(
                code=CODE_VALID, client_id=CLIENT_ID_VALID,
                client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_client(self):
        with self.assertRaises(Exception):
            data = oauth2_token_exchange(
                code=CODE_INVALID, client_id=CLIENT_ID_INVALID,
                client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_secret(self):
        with self.assertRaises(Exception):
            data = oauth2_token_exchange(
                code=CODE_VALID, client_id=CLIENT_ID_VALID,
                client_secret=CLIENT_SECRET_INVALID,
                redirect_uri=REDIRECT_URI)

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__valid_refresh(self):
        data = oauth2_token_exchange(
            refresh_token=REFRESH_TOKEN_VALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {
            'access_token': 'newaccesstoken',
            'expires_in': 36000,
            'refresh_token': 'newrefreshtoken',
            'scope': 'american-gut read wildlife open-humans write '
                     'pgp go-viral',
            'token_type': 'Bearer'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_refresh(self):
        with self.assertRaises(Exception):
            data = oauth2_token_exchange(
                refresh_token=REFRESH_TOKEN_INVALID,
                client_id=CLIENT_ID_VALID,
                client_secret=CLIENT_SECRET_VALID,
                redirect_uri=REDIRECT_URI)


class APITestGetPage(TestCase):
    """
    Tests for :func:`get_page<ohapi.api.get_page>`.
    """

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_get_page_with_results(self):
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
               'exchange-member/?'
               'access_token={}'.format(ACCESS_TOKEN))
        response = get_page(url)
        self.assertEqual(response['project_member_id'], 'PMI')
        self.assertEqual(response['message_permission'], True)
        self.assertEqual(response['data'], [])
        self.assertEqual(response['username'], 'test_user')
        self.assertEqual(response['sources_shared'], [])
        self.assertEqual(response['created'], 'created_date_time')

    @my_vcr.use_cassette()
    def test_get_page_invalid_access_token(self):
        try:
            url = ('https://www.openhumans.org/api/direct-sharing/project/'
                   'exchange-member/?access_token={}'.format("invalid_token"))
            self.assertRaises(Exception, get_page, url)
        except Exception:
            pass


class APITestMessage(TestCase):
    """
    Tests for :func:`message<ohapi.api.message>`.
    """

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_message_valid_access_token(self):
        response = message(subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_message_expired_access_token(self):
        with self.assertRaises(Exception):
            response = message(subject=SUBJECT, message=MESSAGE,
                               access_token=ACCESS_TOKEN_EXPIRED)
            assert response.json() == {"detail": "Expired token."}

    @my_vcr.use_cassette()
    def test_message_invalid_access_token(self):
        with self.assertRaises(Exception):
            response = message(subject=SUBJECT, message=MESSAGE,
                               access_token=ACCESS_TOKEN_INVALID)
            assert response.json() == {"detail": "Invalid token."}

    @my_vcr.use_cassette()
    def test_message_all_members_true_project_member_id_none(self):
        response = message(all_members=True, subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_message_all_members_true_project_member_id_not_none(self):
        self.assertRaises(Exception, message, all_members=True,
                          project_member_ids=['abcdef', 'sdf'],
                          subject=SUBJECT, message=MESSAGE,
                          access_token=ACCESS_TOKEN)

    @my_vcr.use_cassette()
    def test_message_all_members_false_projectmemberid_has_invalid_char(self):
        with self.assertRaises(Exception):
            response = message(project_member_ids=['abcdef1', 'test'],
                               subject=SUBJECT, message=MESSAGE,
                               access_token=MASTER_ACCESS_TOKEN)
            assert response.json() == {"errors":
                                       {"project_member_ids":
                                        ["Project member IDs are always 8" +
                                         " digits long."]}}

    @my_vcr.use_cassette()
    def test_message_all_members_false_projectmemberid_has_invalid_digit(self):
        with self.assertRaises(Exception):
            response = message(project_member_ids=[INVALID_PMI1,
                                                   INVALID_PMI2],
                               subject=SUBJECT, message=MESSAGE,
                               access_token=MASTER_ACCESS_TOKEN)
            assert response.json() == {"errors":
                                       {"project_member_ids":
                                        ["Invalid project member ID(s):" +
                                         " invalidPMI2"]}}

    @my_vcr.use_cassette()
    def test_message_all_members_false_project_member_id_not_none_valid(self):
        response = message(project_member_ids=[VALID_PMI1, VALID_PMI2],
                           subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN)
        self.assertEqual(response.status_code, 200)


class APITestDeleteFile(TestCase):
    """
    Tests for :func:`delete_file<ohapi.api.delete_file>`.
    """

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_delete_file__invalid_access_token(self):
        with self.assertRaises(Exception):
            response = delete_file(
                access_token=ACCESS_TOKEN_INVALID,
                project_member_id='59319749',
                all_files=True)
            assert response.json() == {"detail": "Invalid token."}

    @my_vcr.use_cassette()
    def test_delete_file_project_member_id_given(self):
        response = delete_file(access_token=ACCESS_TOKEN,
                               project_member_id='59319749', all_files=True)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_delete_file_project_member_id_invalid(self):
        with self.assertRaises(Exception):
            response = delete_file(access_token=ACCESS_TOKEN, all_files=True,
                                   project_member_id='1234')
            self.assertEqual(response.status_code, 400)

    @my_vcr.use_cassette()
    def test_delete_file__expired_access_token(self):
        with self.assertRaises(Exception):
            response = delete_file(access_token=ACCESS_TOKEN_EXPIRED,
                                   all_files=True,
                                   project_member_id='59319749')
            assert response.json() == {"detail": "Expired token."}

    @my_vcr.use_cassette()
    def test_delete_file__valid_access_token(self):
        response = delete_file(
            access_token=ACCESS_TOKEN, project_member_id='59319749',
            all_files=True)
        self.assertEqual(response.status_code, 200)


class APITestUpload(TestCase):
    """
    Tests for :func:`upload_file<ohapi.api.upload_file>`.
    """

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_upload_valid_file_valid_access_token(self):
        with patch('%s.open' % __name__, mock_open(), create=True):
            with patch('ohapi.api.open', mock_open(), create=True):
                try:
                    filename = 'foo'

                    def fake_stat(arg):
                        if arg == filename:
                            faked = list(orig_os_stat('/tmp'))
                            faked[stat.ST_SIZE] = len('some stuff')
                            return stat_result(faked)
                        else:
                            return orig_os_stat(arg)
                    orig_os_stat = os.stat
                    os.stat = fake_stat
                    with open('foo', 'w') as h:
                        h.write('some stuff')
                    response = upload_file(target_filepath='foo',
                                           metadata=FILE_METADATA,
                                           access_token=ACCESS_TOKEN,
                                           project_member_id=VALID_PMI1)
                    self.assertEqual(response.status_code, 201)
                    assert response.json() == {"id": "file_id"}
                finally:
                    os.stat = orig_os_stat

    @my_vcr.use_cassette()
    def test_upload_large_file_valid_access_token(self):
        with patch('%s.open' % __name__, mock_open(), create=True):
            with patch('ohapi.api.open', mock_open(), create=True):
                try:
                    filename = 'foo'

                    def fake_stat(arg):
                        if arg == filename:
                            faked = list(orig_os_stat('/tmp'))
                            faked[stat.ST_SIZE] = len('some stuff')
                            return stat_result(faked)
                        else:
                            return orig_os_stat(arg)
                    orig_os_stat = os.stat
                    os.stat = fake_stat
                    with open('foo', 'w') as h:
                        h.write('some stuff')
                    self.assertRaises(Exception, upload_file,
                                      target_filepath='foo',
                                      metadata=FILE_METADATA,
                                      access_token=ACCESS_TOKEN,
                                      project_member_id=VALID_PMI1,
                                      max_bytes=MAX_BYTES)
                except Exception:
                    pass
                finally:
                    os.stat = orig_os_stat

    @my_vcr.use_cassette()
    def test_upload_file_invalid_access_token(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                    response = upload_file(
                        target_filepath='foo',
                        metadata=FILE_METADATA,
                        access_token=ACCESS_TOKEN_INVALID,
                        project_member_id=VALID_PMI1)
                    assert response.json() == {"detail": "Invalid token."}

    @my_vcr.use_cassette()
    def test_upload_file_expired_access_token(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                response = upload_file(
                    target_filepath='foo',
                    metadata=FILE_METADATA,
                    access_token=ACCESS_TOKEN_EXPIRED,
                    project_member_id=VALID_PMI1)
                assert response.json() == {"detail": "Expired token."}

    @my_vcr.use_cassette()
    def test_upload_file_invalid_metadata_with_description(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                response = upload_file(
                    target_filepath='foo',
                    metadata=FILE_METADATA_INVALID_WITH_DESC,
                    access_token=ACCESS_TOKEN,
                    project_member_id=VALID_PMI1)
                assert response.json() == {
                    "metadata":
                    ["\"tags\" is a required " +
                     "field of the metadata"]}

    @my_vcr.use_cassette()
    def test_upload_file_invalid_metadata_without_description(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                response = upload_file(target_filepath='foo',
                                       metadata=FILE_METADATA_INVALID,
                                       access_token=ACCESS_TOKEN,
                                       project_member_id=VALID_PMI1)
                assert response.json() == {
                    "metadata":
                    ["\"description\" is a " +
                     "required field of the metadata"]}

    @my_vcr.use_cassette()
    def test_upload_file_empty(self):
        with self.assertRaises(Exception):
            with patch('%s.open' % __name__, mock_open(), create=True):
                with patch('ohapi.api.open', mock_open(), create=True):
                    try:
                        filename = 'foo'

                        def fake_stat(arg):
                            if arg == filename:
                                faked = list(orig_os_stat('/tmp'))
                                faked[stat.ST_SIZE] = len('some stuff')
                                return stat_result(faked)
                            else:
                                return orig_os_stat(arg)
                        orig_os_stat = os.stat
                        os.stat = fake_stat
                        with open('foo', 'w') as h:
                            h.write('')
                        response = upload_file(target_filepath='foo',
                                               metadata=FILE_METADATA,
                                               access_token=ACCESS_TOKEN,
                                               project_member_id=VALID_PMI1)
                        assert response.json() == {
                            "data_file":
                            ["The submitted file is empty."]}
                    finally:
                        os.stat = orig_os_stat

    def test_upload_file_remote_info_not_none_valid(self):
        with my_vcr.use_cassette('ohapi/cassettes/test_upload_file_' +
                                 'remote_info_not_none_valid.yaml') as cass:
            with patch('%s.open' % __name__, mock_open(), create=True):
                with patch('ohapi.api.open', mock_open(), create=True):
                    try:
                        filename = 'foo'

                        def fake_stat(arg):
                            if arg == filename:
                                faked = list(orig_os_stat('/tmp'))
                                faked[stat.ST_SIZE] = len('some stuff')
                                return stat_result(faked)
                            else:
                                return orig_os_stat(arg)
                        orig_os_stat = os.stat
                        os.stat = fake_stat
                        with open('foo', 'w') as h:
                            h.write('some stuff')
                        upload_file(target_filepath='foo',
                                    metadata=FILE_METADATA,
                                    access_token=ACCESS_TOKEN,
                                    project_member_id=VALID_PMI1,
                                    remote_file_info=REMOTE_FILE_INFO)
                        self.assertEqual(cass.responses[0][
                                         "status"]["code"], 200)
                        self.assertEqual(cass.responses[1][
                                         "status"]["code"], 201)
                        self.assertEqual(cass.responses[1]["body"]["string"]
                                         .decode('utf-8'),
                                         '{"id": "file_id"}')
                    finally:
                        os.stat = orig_os_stat

    def test_upload_file_remote_info_not_none_invalid_access_token(self):
        with my_vcr.use_cassette('ohapi/cassettes/test_upload_file_remote' +
                                 '_info_not_none_invalid_access_' +
                                 'token.yaml') as cass:
            with self.assertRaises(Exception):
                with patch('ohapi.api.open', mock_open(), create=True):
                    upload_file(target_filepath='foo',
                                metadata=FILE_METADATA,
                                access_token=ACCESS_TOKEN_INVALID,
                                project_member_id=VALID_PMI1,
                                remote_file_info=REMOTE_FILE_INFO)
                    self.assertEqual(cass.responses[0][
                                     "status"]["code"], 200)
                    self.assertEqual(
                        cass.responses[1]["body"]["string"]
                        .decode('utf-8'),
                        '{"detail": "Invalid token."}')

    def test_upload_file_remote_info_not_none_expired_access_token(self):
        with my_vcr.use_cassette('ohapi/cassettes/test_upload_file_remote_' +
                                 'info_not_none_expired_access_' +
                                 'token.yaml') as cass:
            with self.assertRaises(Exception):
                with patch('ohapi.api.open', mock_open(), create=True):
                    upload_file(target_filepath='foo',
                                metadata=FILE_METADATA,
                                access_token=ACCESS_TOKEN_EXPIRED,
                                project_member_id=VALID_PMI1,
                                remote_file_info=REMOTE_FILE_INFO)
                    self.assertEqual(cass.responses[0][
                                     "status"]["code"], 200)
                    self.assertEqual(
                        cass.responses[1]["body"]["string"]
                        .decode('utf-8'),
                        '{"detail": "Expired token."}')

    def test_upload_file_empty_remote_info_not_none(self):
        with my_vcr.use_cassette('ohapi/cassettes/test_upload_file_empty_' +
                                 'remote_info_not_none.yaml') as cass:
            with self.assertRaises(Exception):
                with patch('ohapi.api.open', mock_open(), create=True):
                    upload_file(target_filepath='foo',
                                metadata=FILE_METADATA,
                                access_token=ACCESS_TOKEN,
                                project_member_id=VALID_PMI1,
                                remote_file_info=REMOTE_FILE_INFO)
                    self.assertEqual(cass.responses[0][
                                     "status"]["code"], 200)
                    self.assertEqual(
                        cass.responses[1]["body"]["string"]
                        .decode('utf-8'),
                        '{"data_file": ["The submitted file is' +
                        ' empty."]}')

    @my_vcr.use_cassette()
    def test_upload_file_remote_info_not_none_matching_file_size(self):
        with patch('ohapi.api.open', mock_open(), create=True):
            self.assertRaises(Exception, upload_file,
                              target_filepath='foo',
                              metadata=FILE_METADATA,
                              access_token=ACCESS_TOKEN,
                              project_member_id=VALID_PMI1,
                              remote_file_info=REMOTE_FILE_INFO)

    def test_upload_file_remote_info_not_none_invalid_metadata_with_desc(self):
        with my_vcr.use_cassette('ohapi/cassettes/test_upload_file_remote_' +
                                 'info_not_none_invalid_metadata_with_' +
                                 'desc.yaml') as cass:
            with self.assertRaises(Exception):
                with patch('ohapi.api.open', mock_open(), create=True):
                    upload_file(
                        target_filepath='foo',
                        metadata=FILE_METADATA_INVALID_WITH_DESC,
                        access_token=ACCESS_TOKEN,
                        project_member_id=VALID_PMI1,
                        remote_file_info=REMOTE_FILE_INFO)
                    self.assertEqual(cass.responses[0][
                                     "status"]["code"], 200)
                    self.assertEqual(
                        cass.responses[1]["body"]["string"]
                        .decode('utf-8'),
                        '{"metadata":["\\"tags\\" is a required ' +
                        'field of the metadata"]}')

    def test_upload_file_remote_info_not_none_invalid_metadata(self):
        with my_vcr.use_cassette(
                'ohapi/cassettes/test_upload_file_remote_in' +
                'fo_not_none_invalid_metadata.yaml') as cass:
            with self.assertRaises(Exception):
                with patch('ohapi.api.open', mock_open(), create=True):
                    upload_file(target_filepath='foo',
                                metadata=FILE_METADATA_INVALID,
                                access_token=ACCESS_TOKEN,
                                project_member_id=VALID_PMI1,
                                remote_file_info=REMOTE_FILE_INFO)
                    self.assertEqual(cass.responses[0][
                                     "status"]["code"], 200)
                    self.assertEqual(
                        cass.responses[1]["body"]["string"]
                        .decode('utf-8'),
                        '{"metadata":["\\"description\\" is a ' +
                        'required field of the metadata"]}')


class APITestUploadAws(TestCase):
    """
    Tests for :func:`upload_aws<ohapi.api.upload_aws>`.
    """

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_upload_aws_invalid_access_token(self):
        with self.assertRaises(Exception):
            response = upload_aws(
                target_filepath='foo',
                metadata=FILE_METADATA,
                access_token=ACCESS_TOKEN_INVALID,
                project_member_id=VALID_PMI1)
            assert response.json() == {"detail": "Invalid token."}

    @my_vcr.use_cassette()
    def test_upload_aws_expired_access_token(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                response = upload_aws(
                    target_filepath='foo',
                    metadata=FILE_METADATA,
                    access_token=ACCESS_TOKEN_EXPIRED,
                    project_member_id=VALID_PMI1)
                assert response.json() == {"detail": "Expired token."}

    @my_vcr.use_cassette()
    def test_upload_aws_invalid_metadata_with_description(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                response = upload_aws(
                    target_filepath='foo',
                    metadata=FILE_METADATA_INVALID_WITH_DESC,
                    access_token=ACCESS_TOKEN,
                    project_member_id=VALID_PMI1)
                assert response.json() == {
                    "metadata":
                    ["\"tags\" is a required " +
                     "field of the metadata"]}

    @my_vcr.use_cassette()
    def test_upload_aws_invalid_metadata_without_description(self):
        with self.assertRaises(Exception):
            with patch('ohapi.api.open', mock_open(), create=True):
                response = upload_aws(
                    target_filepath='foo',
                    metadata=FILE_METADATA_INVALID_WITHOUT_DESC,
                    access_token=ACCESS_TOKEN,
                    project_member_id=VALID_PMI1)
                assert response.json() == {
                    "metadata":
                    ["\"description\" is a " +
                     "required field of the metadata"]}

    def test_upload_aws_valid_access_token(self):
        with my_vcr.use_cassette('ohapi/cassettes/test_upload_aws_valid_' +
                                 'access_token') as cass:
            with patch('ohapi.api.open', mock_open(read_data=b'some stuff')):
                try:

                    def fake_stat(arg):
                        if arg == "foo":
                            faked = list(orig_os_stat('/tmp'))
                            faked[stat.ST_SIZE] = len('some stuff')
                            return stat_result(faked)
                        else:
                            return orig_os_stat(arg)
                    orig_os_stat = os.stat
                    os.stat = fake_stat
                    upload_aws(target_filepath='foo',
                               metadata=FILE_METADATA,
                               access_token=ACCESS_TOKEN,
                               project_member_id=VALID_PMI1
                               )
                    self.assertEqual(cass.responses[0][
                                     "status"]["code"], 201)
                    self.assertEqual(cass.responses[1][
                                     "status"]["code"], 200)
                    self.assertEqual(cass.responses[2][
                                     "status"]["code"], 200)
                finally:
                    os.stat = orig_os_stat
                    pass
