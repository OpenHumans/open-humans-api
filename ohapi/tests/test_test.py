from unittest import TestCase
from ohapi.utils_fs import (guess_tags, load_metadata_csv, validate_metadata)


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
