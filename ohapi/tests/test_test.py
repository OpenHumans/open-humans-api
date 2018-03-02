from unittest import TestCase
from ohapi.utils_fs import guess_tags


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
