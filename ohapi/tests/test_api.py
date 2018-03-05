from unittest import TestCase

import pytest
import vcr

from ohapi.api import (
    SettingsError, oauth2_auth_url, oauth2_token_exchange)

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes')


class APITest(TestCase):

    TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE = {
        'client_id': 'clientid',
        'client_secret': 'clientsecret',
        'redirect_uri': 'http://127.0.0.1:5000/authorize_openhumans/',
    }

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
            code='codegoeshere', **self.TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE)
        assert data == {
            'access_token': 'returnedaccesstoken',
            'expires_in': 36000,
            'refresh_token': 'returnedrefreshtoken',
            'scope': 'american-gut read wildlife open-humans write '
                     'pgp go-viral',
            'token_type': 'Bearer'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_code(self):
        data = oauth2_token_exchange(
            code='codegoeshere', **self.TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE)
        assert data == {'error': 'invalid_grant'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_client(self):
        data = oauth2_token_exchange(
            code='codegoeshere', **self.TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE)
        assert data == {'error': 'invalid_client'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_secret(self):
        data = oauth2_token_exchange(
            code='codegoeshere', **self.TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE)
        assert data == {'error': 'invalid_client'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__valid_refresh(self):
        data = oauth2_token_exchange(
            refresh_token='refreshtokengoeshere',
            **self.TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE)
        assert data == {
            'access_token': 'newaccesstoken',
            'expires_in': 36000,
            'refresh_token': 'newrefreshtoken',
            'scope': 'american-gut read wildlife open-humans write '
                     'pgp go-viral',
            'token_type': 'Bearer'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_refresh(self):
        data = oauth2_token_exchange(
            refresh_token='refreshtokengoeshere',
            **self.TESTING_KWARGS_OAUTH2_TOKEN_EXCHANGE)
        assert data == {'error': 'invalid_grant'}
