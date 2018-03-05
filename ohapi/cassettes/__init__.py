"""
VCR records of Open Humans API calls.

Example usage:

>>> from ohapi.cassettes import get_vcr
>>> from ohapi.api import oauth2_token_exchange
>>> with ohapi_vcr.use_cassette('test_oauth2_token_exchange__valid_code'):
        oauth2_token_exchange(
            client_id='clientid', client_secret='clientsecret',
            redirect_uri='http://127.0.0.1:5000/authorize/',
            code='codegoeshere')

{'token_type': 'Bearer', 'access_token': 'returnedaccesstoken',
'refresh_token': 'returnedrefreshtoken', 'expires_in': 36000,
'scope': 'american-gut read wildlife open-humans write pgp go-viral'}
"""
import os

import vcr


def valid_cassettes():
    base_dir = os.path.dirname(__file__)
    return [x for x in os.listdir(base_dir) if x.endswith('.yaml')]


def get_vcr():
    base_dir = os.path.dirname(__file__)
    my_vcr = vcr.VCR(record_mode='none',
                     path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                     cassette_library_dir=base_dir)
    return my_vcr
