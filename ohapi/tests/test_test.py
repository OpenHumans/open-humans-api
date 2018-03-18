from unittest import TestCase
from ohapi.utils_fs import (guess_tags, load_metadata_csv,
                            validate_metadata, characterize_local_files,
                            read_id_list)
from humanfriendly import parse_size
import arrow
import os

MAX_FILE_DEFAULT = parse_size('128m')


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

    def test_characterize_local_files(self):
        filename = 'file_1.json'
        filedir = 'ohapi/tests/data/test_directory/'
        response = characterize_local_files(
            filedir, max_bytes=MAX_FILE_DEFAULT)
        filepath = os.path.join(filedir, filename)
        file_stats = os.stat(filepath)
        CREATION_DATE = arrow.get(file_stats.st_ctime).isoformat()
        self.assertEqual(response,
                         {
                             'file_2.json':
                             {'md5': 'd41d8cd98f00b204e9800998ecf8427e',
                              'creation_date': CREATION_DATE,
                              'description': '',
                              'tags': ['json']},
                             'file_1.json':
                             {'md5': 'd41d8cd98f00b204e9800998ecf8427e',
                                 'creation_date': CREATION_DATE,
                                 'description': '',
                                 'tags': ['json']}})

    def test_read_id_list_filepath_not_given(self):
        response = read_id_list(filepath=None)
        self.assertEqual(response, None)

    def test_read_id_list_filepath_given(self):
        filename = 'sample.txt'
        filedir = 'ohapi/tests/data/test_id_dir/'
        FILEPATH = os.path.join(filedir, filename)
        response = read_id_list(filepath=FILEPATH)
        self.assertEqual(response, ['12345678'])
