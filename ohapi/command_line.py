import csv
import logging
import os
import re

import click

from click import UsageError

from humanfriendly import parse_size

from .api import (OH_BASE_URL, exchange_oauth2_member, message,
                  delete_file, oauth2_auth_url,
                  oauth2_token_exchange)

from .projects import OHProject
from .public import download as public_download
from .utils_fs import load_metadata_csv, mk_metadata_csv, read_id_list
from .utils_fs import review_metadata_csv

MAX_FILE_DEFAULT = parse_size('128m')


def set_log_level(debug, verbose):
    """
    Function for setting the logging level.

    :param debug: This boolean field is the logging level.
    :param verbose: This boolean field is the logging level.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)


@click.command()
@click.option('-d', '--directory',
              help='Target directory for downloaded files.', required=True)
@click.option('-T', '--master-token', help='Project master access token.')
@click.option('-m', '--member', help='Project member ID.')
@click.option('-t', '--access-token', help='OAuth2 user access token.')
@click.option('-s', '--source', help='Only download files from this source.')
@click.option('--project-data', help="Download this project's own data.",
              is_flag=True)
@click.option('--max-size', help='Maximum file size to download.',
              default='128m', show_default=True)
@click.option('-v', '--verbose', help='Report INFO level logging to stdout',
              is_flag=True)
@click.option('--debug', help='Report DEBUG level logging to stdout.',
              is_flag=True)
@click.option('--memberlist', help='Text file with whitelist IDs to retrieve')
@click.option('--excludelist', help='Text file with blacklist IDs to avoid')
@click.option('--id-filename', is_flag=True,
              help='Prepend filenames with IDs to ensure uniqueness.')
def download_cli(directory, master_token=None, member=None, access_token=None,
                 source=None, project_data=False, max_size='128m',
                 verbose=False, debug=False, memberlist=None,
                 excludelist=None, id_filename=False):
    """
    Command line function for downloading data from project members to the
    target directory. For more information visit
    :func:`download<ohapi.command_line.download>`.
    """
    return download(directory, master_token, member, access_token, source,
                    project_data, max_size, verbose, debug, memberlist,
                    excludelist, id_filename)


def download(directory, master_token=None, member=None, access_token=None,
             source=None, project_data=False, max_size='128m', verbose=False,
             debug=False, memberlist=None, excludelist=None,
             id_filename=False):
    """
    Download data from project members to the target directory.

    Unless this is a member-specific download, directories will be
    created for each project member ID. Also, unless a source is specified,
    all shared sources are downloaded and data is sorted into subdirectories
    according to source.

    Projects can optionally return data to Open Humans member accounts.
    If project_data is True (or the "--project-data" flag is used), this data
    (the project's own data files, instead of data from other sources) will be
    downloaded for each member.

    :param directory: This field is the target directory to download data.
    :param master_token: This field is the master access token for the project.
        It's default value is None.
    :param member: This field is specific member whose project data is
        downloaded. It's default value is None.
    :param access_token: This field is the user specific access token. It's
        default value is None.
    :param source: This field is the data source. It's default value is None.
    :param project_data: This field is data related to particular project. It's
        default value is False.
    :param max_size: This field is the maximum file size. It's default value is
        128m.
    :param verbose: This boolean field is the logging level. It's default value
        is False.
    :param debug: This boolean field is the logging level. It's default value
        is False.
    :param memberlist: This field is list of members whose data will be
        downloaded. It's default value is None.
    :param excludelist: This field is list of members whose data will be
        skipped. It's default value is None.
    """
    set_log_level(debug, verbose)

    if (memberlist or excludelist) and (member or access_token):
        raise UsageError('Please do not provide a memberlist or excludelist '
                         'when retrieving data for a single member.')
    memberlist = read_id_list(memberlist)
    excludelist = read_id_list(excludelist)
    if not (master_token or access_token) or (master_token and access_token):
        raise UsageError('Please specify either a master access token (-T), '
                         'or an OAuth2 user access token (-t).')
    if (source and project_data):
        raise UsageError("It doesn't make sense to use both 'source' and"
                         "'project-data' options!")

    if master_token:
        project = OHProject(master_access_token=master_token)
        if member:
            if project_data:
                project.download_member_project_data(
                    member_data=project.project_data[member],
                    target_member_dir=directory,
                    max_size=max_size,
                    id_filename=id_filename)
            else:
                project.download_member_shared(
                    member_data=project.project_data[member],
                    target_member_dir=directory,
                    source=source,
                    max_size=max_size,
                    id_filename=id_filename)
        else:
            project.download_all(target_dir=directory,
                                 source=source,
                                 max_size=max_size,
                                 memberlist=memberlist,
                                 excludelist=excludelist,
                                 project_data=project_data,
                                 id_filename=id_filename)
    else:
        member_data = exchange_oauth2_member(access_token, all_files=True)
        if project_data:
            OHProject.download_member_project_data(member_data=member_data,
                                                   target_member_dir=directory,
                                                   max_size=max_size,
                                                   id_filename=id_filename)
        else:
            OHProject.download_member_shared(member_data=member_data,
                                             target_member_dir=directory,
                                             source=source,
                                             max_size=max_size,
                                             id_filename=id_filename)


@click.command()
@click.option('-T', '--master-token', help='Project master access token.',
              required=True)
@click.option('-v', '--verbose', help='Show INFO level logging', is_flag=True)
@click.option('--debug', help='Show DEBUG level logging.', is_flag=True)
@click.option('--output-csv', help="Output project metedata CSV",
              required=True)
def download_metadata_cli(master_token, output_csv, verbose=False,
                          debug=False):
    """
    Command line function for downloading metadata.
    For more information visit
    :func:`download_metadata<ohapi.command_line.download_metadata>`.
    """
    return download_metadata(master_token, output_csv, verbose, debug)


def download_metadata(master_token, output_csv, verbose=False, debug=False):
    """
    Output CSV with metadata for a project's downloadable files in Open Humans.

    :param master_token: This field is the master access token for the project.
    :param output_csv: This field is the target csv file to which metadata is
        written.
    :param verbose: This boolean field is the logging level. It's default value
        is False.
    :param debug: This boolean field is the logging level. It's default value
        is False.
    """
    set_log_level(debug, verbose)

    project = OHProject(master_access_token=master_token)

    with open(output_csv, 'w') as f:
        csv_writer = csv.writer(f)
        header = ['project_member_id', 'data_source', 'file_basename',
                  'file_upload_date']
        csv_writer.writerow(header)
        for member_id in project.project_data:
            if not project.project_data[member_id]['data']:
                csv_writer.writerow([member_id, 'NA', 'None', 'NA'])
            else:
                for data_item in project.project_data[member_id]['data']:
                    logging.debug(data_item)
                    csv_writer.writerow([
                        member_id, data_item['source'],
                        data_item['basename'].encode('utf-8'),
                        data_item['created']])


@click.command()
@click.option('-d', '--directory', help='Target directory', required=True)
@click.option('--create-csv', help='Create draft CSV metadata', required=False)
@click.option('--review', help='Review existing metadata file', required=False)
@click.option('--max-size', help='Maximum file size to consider.',
              default='128m', show_default=True)
@click.option('-v', '--verbose', help='Show INFO level logging', is_flag=True)
@click.option('--debug', help='Show DEBUG level logging.', is_flag=True)
def upload_metadata_cli(directory, create_csv='', review='',
                        max_size='128m', verbose=False, debug=False):
    """
    Command line function for drafting or reviewing metadata files.
    For more information visit
    :func:`upload_metadata<ohapi.command_line.upload_metadata>`.
    """
    return upload_metadata(directory, create_csv, review,
                           max_size, verbose, debug)


def upload_metadata(directory, create_csv='', review='',
                    max_size='128m', verbose=False, debug=False):
    """
    Draft or review metadata files for uploading files to Open Humans.
    The target directory should either represent files for a single member (no
    subdirectories), or contain a subdirectory for each project member ID.

    :param directory: This field is the directory for which metadata has to be
        created.
    :param create_csv: This field is the output filepath to which csv file
        will be written.
    :param max_size: This field is the maximum file size. It's default value is
        None.
    :param verbose: This boolean field is the logging level. It's default value
        is False.
    :param debug: This boolean field is the logging level. It's default value
        is False.
    """
    set_log_level(debug, verbose)

    max_bytes = parse_size(max_size)
    if create_csv and review:
        raise ValueError("Either create_csv must be true or review must be " +
                         "true but not both")
    if review:
        if review_metadata_csv(directory, review):
            print("The metadata file has been reviewed and is valid.")
    elif create_csv:
        mk_metadata_csv(directory, create_csv, max_bytes=max_bytes)
    else:
        raise ValueError("Either create_csv must be true or review must be " +
                         "true but not both should be false")


@click.command()
@click.option('-d', '--directory',
              help='Target directory for downloaded files.', required=True)
@click.option('--metadata-csv', help='CSV file containing file metadata.',
              required=True)
@click.option('-T', '--master-token', help='Project master access token.')
@click.option('-m', '--member', help='Project member ID.')
@click.option('-t', '--access-token', help='OAuth2 user access token.')
@click.option('--safe', help='Do not overwrite files in Open Humans.',
              is_flag=True)
@click.option('--sync', help='Delete files not present in local directories.',
              is_flag=True)
@click.option('--max-size', help='Maximum file size to download.',
              default='128m', show_default=True)
@click.option('-v', '--verbose', help='Report INFO level logging to stdout',
              is_flag=True)
@click.option('--debug', help='Report DEBUG level logging to stdout.',
              is_flag=True)
def upload_cli(directory, metadata_csv, master_token=None, member=None,
               access_token=None, safe=False, sync=False, max_size='128m',
               mode='default', verbose=False, debug=False):
    """
    Command line function for uploading files to OH.
    For more information visit
    :func:`upload<ohapi.command_line.upload>`.
    """
    return upload(directory, metadata_csv, master_token, member,
                  access_token, safe, sync, max_size,
                  mode, verbose, debug)


def upload(directory, metadata_csv, master_token=None, member=None,
           access_token=None, safe=False, sync=False, max_size='128m',
           mode='default', verbose=False, debug=False):
    """
    Upload files for the project to Open Humans member accounts.

    If using a master access token and not specifying member ID:

    (1) Files should be organized in subdirectories according to project
    member ID, e.g.:

        main_directory/01234567/data.json
        main_directory/12345678/data.json
        main_directory/23456789/data.json

    (2) The metadata CSV should have the following format:

        1st column: Project member ID
        2nd column: filenames
        3rd & additional columns: Metadata fields (see below)

    If uploading for a specific member:
    (1) The local directory should not contain subdirectories.
    (2) The metadata CSV should have the following format:
    1st column: filenames
    2nd & additional columns: Metadata fields (see below)

    The default behavior is to overwrite files with matching filenames on
    Open Humans, but not otherwise delete files. (Use --safe or --sync to
    change this behavior.)

    If included, the following metadata columns should be correctly formatted:
    'tags': should be comma-separated strings
    'md5': should match the file's md5 hexdigest
    'creation_date', 'start_date', 'end_date': ISO 8601 dates or datetimes

    Other metedata fields (e.g. 'description') can be arbitrary strings.
    Either specify sync as True or safe as True but not both.

    :param directory: This field is the target directory from which data will
        be uploaded.
    :param metadata_csv: This field is the filepath of the metadata csv file.
    :param master_token: This field is the master access token for the project.
        It's default value is None.
    :param member: This field is specific member whose project data is
        downloaded. It's default value is None.
    :param access_token: This field is the user specific access token. It's
        default value is None.
    :param safe: This boolean field will overwrite matching filename. It's
        default value is False.
    :param sync: This boolean field will delete files on Open Humans that are
        not in the local directory. It's default value is False.
    :param max_size: This field is the maximum file size. It's default value is
        None.
    :param mode: This field takes three value default, sync, safe. It's default
        value is 'default'.
    :param verbose: This boolean field is the logging level. It's default value
        is False.
    :param debug: This boolean field is the logging level. It's default value
        is False.
    """
    if safe and sync:
        raise UsageError('Safe (--safe) and sync (--sync) modes are mutually '
                         'incompatible!')
    if not (master_token or access_token) or (master_token and access_token):
        raise UsageError('Please specify either a master access token (-T), '
                         'or an OAuth2 user access token (-t).')

    set_log_level(debug, verbose)

    if sync:
        mode = 'sync'
    elif safe:
        mode = 'safe'

    metadata = load_metadata_csv(metadata_csv)

    subdirs = [i for i in os.listdir(directory) if
               os.path.isdir(os.path.join(directory, i))]
    if subdirs:
        if not all([re.match(r'^[0-9]{8}$', d) for d in subdirs]):
            raise UsageError(
                "Subdirs expected to match project member ID format!")
        if (master_token and member) or not master_token:
            raise UsageError(
                "Subdirs shouldn't exist if uploading for specific member!")
        project = OHProject(master_access_token=master_token)
        for member_id in subdirs:
            subdir_path = os.path.join(directory, member_id)
            project.upload_member_from_dir(
                member_data=project.project_data[member_id],
                target_member_dir=subdir_path,
                metadata=metadata[member_id],
                mode=mode,
                access_token=project.master_access_token,
            )
    else:
        if master_token and not (master_token and member):
            raise UsageError('No member specified!')
        if master_token:
            project = OHProject(master_access_token=master_token)
            project.upload_member_from_dir(
                member_data=project.project_data[member],
                target_member_dir=directory,
                metadata=metadata,
                mode=mode,
                access_token=project.master_access_token,
            )
        else:
            member_data = exchange_oauth2_member(access_token)
            OHProject.upload_member_from_dir(
                member_data=member_data,
                target_member_dir=directory,
                metadata=metadata,
                mode=mode,
                access_token=access_token,
            )


@click.command()
@click.option('-cid', '--client_id',
              help='client id of user.', required=True)
@click.option('-cs', '--client_secret',
              help='client secret of user.', required=True)
@click.option('-re_uri', '--redirect_uri',
              help='redirect_uri of user', required=True)
@click.option('--base_url', help='base url of Open Humans',
              default=OH_BASE_URL, show_default=True)
@click.option('--code', help='code of user',
              default=None, show_default=True)
@click.option('-rt', '--refresh_token', help='refresh token of user',
              default=None, show_default=True)
def oauth_token_exchange_cli(client_id, client_secret, redirect_uri,
                             base_url=OH_BASE_URL, code=None,
                             refresh_token=None):
    """
    Command line function for obtaining the refresh token/code.
    For more information visit
    :func:`oauth2_token_exchange<ohapi.api.oauth2_token_exchange>`.
    """
    print(oauth2_token_exchange(client_id, client_secret, redirect_uri,
                                base_url, code, refresh_token))

@click.command()
@click.option('-r', '--redirect_uri',
              help='Redirect URL for project')
@click.option('-c', '--client_id',
              help='Client ID for project', required=True)
@click.option('--base_url', help='Base URL', default=OH_BASE_URL)
def oauth2_auth_url_cli(redirect_uri=None, client_id=None,
                        base_url=OH_BASE_URL):
    """
    Command line function for obtaining the Oauth2 url.
    For more information visit
    :func:`oauth2_auth_url<ohapi.api.oauth2_auth_url>`.
    """
    result = oauth2_auth_url(redirect_uri, client_id, base_url)
    print('The requested URL is : \r')
    print(result)


@click.command()
@click.option('-s', '--subject', help='subject', required=True)
@click.option('-m', '--message_body', help='compose message', required=True)
@click.option('-at', '--access_token', help='access token', required=True)
@click.option('--all_members', help='all members',
              default=False, show_default=True)
@click.option('--project_member_ids',
              help='list of comma-separated project_member_ids. ' +
              'Example argument: "ID1, ID2"',
              default=None, show_default=True)
@click.option('-v', '--verbose', help='Show INFO level logging', is_flag=True)
@click.option('--debug', help='Show DEBUG level logging.', is_flag=True)
def message_cli(subject, message_body, access_token, all_members=False,
                project_member_ids=None, base_url=OH_BASE_URL,
                verbose=False, debug=False):
    """
    Command line function for sending email to a single user or in bulk.
    For more information visit
    :func:`message<ohapi.api.message>`.

    """
    if project_member_ids:
        project_member_ids = re.split(r'[ ,\r\n]+', project_member_ids)
    return message(subject, message_body, access_token, all_members,
                   project_member_ids, base_url)


@click.command()
@click.option('-T', '--access_token', help='Access token', required=True)
@click.option('-m', '--project_member_id', help='Project Member ID',
              required=True)
@click.option('-b', '--file_basename', help='File basename')
@click.option('-i', '--file_id', help='File ID')
@click.option('--all_files', help='Delete all files',
              default=False, show_default=True)
def delete_cli(access_token, project_member_id, base_url=OH_BASE_URL,
               file_basename=None, file_id=None, all_files=False):
    """
    Command line function for deleting files.
    For more information visit
    :func:`delete_file<ohapi.api.delete_file>`.
    """
    response = delete_file(access_token, project_member_id,
                           base_url, file_basename, file_id, all_files)
    if (response.status_code == 200):
        print("File deleted successfully")
    else:
        print("Bad response while deleting file.")


@click.command()
@click.option('-s', '--source', help='the source to download files from')
@click.option('-u', '--username', help='the user to download files from')
@click.option('-d', '--directory', help='the directory for downloaded files',
              default='.')
@click.option('-m', '--max-size', help='the maximum file size to download',
              default='128m')
@click.option('-q', '--quiet', help='Report ERROR level logging to stdout',
              is_flag=True)
@click.option('--debug', help='Report DEBUG level logging to stdout.',
              is_flag=True)
def public_data_download_cli(source, username, directory, max_size, quiet,
                             debug):
    """
    Command line tools for downloading public data.
    """
    return public_download(source, username, directory, max_size, quiet, debug)
