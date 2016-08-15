import logging
import os

import arrow
from humanfriendly import parse_size

from .utils import get_all_results, download_file

MAX_SIZE_DEFAULT = '128m'


class OHProject:
    """
    Work with an Open Humans Project.
    """
    def __init__(self, master_access_token):
        self.master_access_token = master_access_token
        self.project_data = None
        self.update_data()

    def update_data(self):
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
               'members/?access_token={}'.format(self.master_access_token))
        results = get_all_results(url)
        self.project_data = {result['project_member_id']: result for
                             result in results}

    @staticmethod
    def download_member_to_dir(member_data, target_member_dir,
                               max_size=MAX_SIZE_DEFAULT):
        """
        Download files to sync a local directory to match OH member data.

        Files are downloaded to match their "basename" on Open Humans.
        If there are multiple files with the same name, the most recent is
        downloaded.
        """
        logging.info('in download_member_to_dir')
        file_data = {}
        for datafile in member_data['data']:
            basename = datafile['basename']
            if (basename not in file_data or
                    arrow.get(datafile['created']) >
                    arrow.get(file_data[basename]['created'])):
                file_data[basename] = datafile
        for basename in file_data:
            source = file_data[basename]['source']
            source_data_dir = os.path.join(target_member_dir, source)
            if not os.path.exists(source_data_dir):
                os.mkdir(source_data_dir)
            target_filepath = os.path.join(source_data_dir, basename)
            download_file(download_url=file_data[basename]['download_url'],
                          target_filepath=target_filepath,
                          max_bytes=parse_size(max_size))

    def download_to_dir(self, target_dir, project_member=None,
                        all_members=False, max_size=MAX_SIZE_DEFAULT):
        if not (project_member or all_members):
            raise Exception('Specify member ID, or set all_members to True.')
        if all_members:
            members = self.project_data.keys()
            for member in members:
                member_dir = os.path.join(target_dir, member)
                if not os.path.exists(member_dir):
                    os.mkdir(member_dir)
                self.download_member_to_dir(
                    member_data=self.project_data[member],
                    target_member_dir=member_dir,
                    max_size=max_size)
        else:
            self.download_member_to_dir(
                member_data=self.project_data[project_member],
                target_member_dir=target_dir,
                max_size=max_size)
