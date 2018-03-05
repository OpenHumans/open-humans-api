from unittest import TestCase

from ohapi.cassettes import get_vcr, valid_cassettes


class CasettesTest(TestCase):
    def setUp(self):
        pass

    def test_get_vcr(self):
        get_vcr()

    def test_valid_cassettes(self):
        valid_cassettes()
