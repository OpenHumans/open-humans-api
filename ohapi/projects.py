import logging
import os

import arrow
from humanfriendly import parse_size

from .api import delete_file, get_all_results, upload_aws
from .utils_fs import download_file, validate_metadata

MAX_SIZE_DEFAULT = '128m'


class OHProject:
    """
    Work with an Open Humans Project.
    """
    def __init__(self, master_access_token):
        self.master_access_token = master_access_token
        self.project_data = None
        self.update_data()

    @staticmethod
    def _get_member_file_data(member_data):
        """
        Helper function to get file data of member of a project.

        :param member_data: This field is data related to member in a project.
        """
        file_data = {}
        for datafile in member_data['data']:
            basename = datafile['basename']
            if (basename not in file_data or
                    arrow.get(datafile['created']) >
                    arrow.get(file_data[basename]['created'])):
                file_data[basename] = datafile
        return file_data

    def update_data(self):
        """
        Returns data for all users including shared data files.
        """
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
               'members/?access_token={}'.format(self.master_access_token))
        results = get_all_results(url)
        self.project_data = {result['project_member_id']: result for
                             result in results}
        return self.project_data

    @classmethod
    def download_member_project_data(cls, member_data, target_member_dir,
                                     max_size=MAX_SIZE_DEFAULT):
        """
        Download files to sync a local dir to match OH member project data.

        :param member_data: This field is data related to member in a project.
        :param target_member_dir: This field is the target directory where data
            will be downloaded.
        :param max_size: This field is the maximum file size. It's default
            value is 128m.
        """
        logging.debug('Download member project data...')
        sources_shared = member_data['sources_shared']
        file_data = cls._get_member_file_data(member_data)
        for basename in file_data:
            # This is using a trick to identify a project's own data in an API
            # response, without knowing the project's identifier: if the data
            # isn't a shared data source, it must be the project's own data.
            if file_data[basename]['source'] in sources_shared:
                continue
            target_filepath = os.path.join(target_member_dir, basename)
            download_file(download_url=file_data[basename]['download_url'],
                          target_filepath=target_filepath,
                          max_bytes=parse_size(max_size))

    @classmethod
    def download_member_shared(cls, member_data, target_member_dir, source=None,
                               max_size=MAX_SIZE_DEFAULT):
        """
        Download files to sync a local dir to match OH member shared data.

        Files are downloaded to match their "basename" on Open Humans.
        If there are multiple files with the same name, the most recent is
        downloaded.

        :param member_data: This field is data related to member in a project.
        :param target_member_dir: This field is the target directory where data
            will be downloaded.
        :param source: This field is the source from which to download data.
        :param max_size: This field is the maximum file size. It's default
            value is 128m.
        """
        logging.debug('Download member shared data...')
        sources_shared = member_data['sources_shared']
        file_data = cls._get_member_file_data(member_data)

        logging.info('Downloading member data to {}'.format(target_member_dir))
        for basename in file_data:

            # If not in sources shared, it's the project's own data. Skip.
            if file_data[basename]['source'] not in sources_shared:
                continue

            # Filter source if specified. Determine target directory for file.
            if source:
                if source == file_data[basename]['source']:
                    target_filepath = os.path.join(target_member_dir, basename)
                else:
                    continue
            else:
                source_data_dir = os.path.join(target_member_dir,
                                               file_data[basename]['source'])
                if not os.path.exists(source_data_dir):
                    os.mkdir(source_data_dir)
                target_filepath = os.path.join(source_data_dir, basename)

            download_file(download_url=file_data[basename]['download_url'],
                          target_filepath=target_filepath,
                          max_bytes=parse_size(max_size))

    def download_all(self, target_dir, source=None, project_data=False,
                     memberlist=None, excludelist=None,
                     max_size=MAX_SIZE_DEFAULT):
        """
        Download data for all users including shared data files.

        :param target_dir: This field is the target directory to download data.
        :param source: This field is the data source. It's default value is
            None.
        :param project_data: This field is data related to particular project.
            It's default value is False.
        :param memberlist: This field is list of members whose data will be
            downloaded. It's default value is None.
        :param excludelist: This field is list of members whose data will be
            skipped. It's default value is None.
        :param max_size: This field is the maximum file size. It's default
            value is 128m.
        """
        members = self.project_data.keys()
        for member in members:
            if not (memberlist is None) and member not in memberlist:
                logging.debug('Skipping {}, not in memberlist'.format(member))
                continue
            if excludelist and member in excludelist:
                logging.debug('Skipping {}, in excludelist'.format(member))
                continue
            member_dir = os.path.join(target_dir, member)
            if not os.path.exists(member_dir):
                os.mkdir(member_dir)
            if project_data:
                self.download_member_project_data(
                    member_data=self.project_data[member],
                    target_member_dir=member_dir,
                    max_size=max_size)
            else:
                self.download_member_shared(
                    member_data=self.project_data[member],
                    target_member_dir=member_dir,
                    source=source,
                    max_size=max_size)

    @staticmethod
    def upload_member_from_dir(member_data, target_member_dir, metadata,
                               access_token, mode='default',
                               max_size=MAX_SIZE_DEFAULT):
        """
        Upload files in target directory to an Open Humans member's account.

        The default behavior is to overwrite files with matching filenames on
        Open Humans, but not otherwise delete files.

        If the 'mode' parameter is 'safe': matching filenames will not be
        overwritten.

        If the 'mode' parameter is 'sync': files on Open Humans that are not
        in the local directory will be deleted.

        :param member_data: This field is data related to member in a project.
        :param target_member_dir: This field is the target directory from where
            data will be uploaded.
        :param metadata: This field is metadata for files to be uploaded.
        :param access_token: This field is user specific access token.
        :param mode: This field takes three value default, sync, safe. It's
            default value is 'default'.
        :param max_size: This field is the maximum file size. It's default
            value is 128m.
        """
        if not validate_metadata(target_member_dir, metadata):
            raise ValueError('Metadata should match directory contents!')
        project_data = {f['basename']: f for f in member_data['data'] if
                        f['source'] not in member_data['sources_shared']}
        for filename in metadata:
            if filename in project_data and mode == 'safe':
                logging.info('Skipping {}, remote exists with matching'
                             ' name'.format(filename))
                continue
            filepath = os.path.join(target_member_dir, filename)
            remote_file_info = (project_data[filename] if filename in
                                project_data else None)
            upload_aws(target_filepath=filepath,
                       metadata=metadata[filename],
                       access_token=access_token,
                       project_member_id=member_data['project_member_id'],
                       remote_file_info=remote_file_info)
        if mode == 'sync':
            for filename in project_data:
                if filename not in metadata:
                    logging.debug("Deleting {}".format(filename))
                    delete_file(
                        file_basename=filename,
                        access_token=access_token,
                        project_member_id=member_data['project_member_id'])
