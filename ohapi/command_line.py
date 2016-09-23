import csv
import logging
import os
import re

import click
from click import UsageError
from humanfriendly import parse_size

from .projects import OHProject
from .utils import exchange_oauth2_member, load_metadata_csv, mk_metadata_csv

MAX_FILE_DEFAULT = parse_size('128m')


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
def download(directory, master_token=None, member=None, access_token=None,
             source=None, project_data=False, max_size='128m', verbose=False,
             debug=False):
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
    """
    if not (master_token or access_token) or (master_token and access_token):
        raise UsageError('Please specify either a master access token (-T), '
                         'or an OAuth2 user access token (-t).')
    if (source and project_data):
        raise UsageError("It doesn't make sense to use both 'source' and"
                         "'project-data' options!")

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    if master_token:
        project = OHProject(master_access_token=master_token)
        if member:
            if project_data:
                project.download_member_project_data(
                    member_data=project.project_data[member],
                    target_member_dir=directory,
                    max_size=max_size)
            else:
                project.download_member_shared(
                    member_data=project.project_data[member],
                    target_member_dir=directory,
                    source=source,
                    max_size=max_size)
        else:
            project.download_all(target_dir=directory,
                                 source=source,
                                 max_size=max_size,
                                 project_data=project_data)
    else:
        member_data = exchange_oauth2_member(access_token)
        if project_data:
            OHProject.download_member_project_data(member_data=member_data,
                                                   target_member_dir=directory,
                                                   max_size=max_size)
        else:
            OHProject.download_member_shared(member_data=member_data,
                                             target_member_dir=directory,
                                             source=source,
                                             max_size=max_size)


@click.command()
@click.option('-T', '--master-token', help='Project master access token.',
              required=True)
@click.option('-v', '--verbose', help='Show INFO level logging', is_flag=True)
@click.option('--debug', help='Show DEBUG level logging.', is_flag=True)
@click.option('--output-csv', help="Output project metedata CSV",
              required=True)
def download_metadata(master_token, output_csv, verbose=False, debug=False):
    """
    Output CSV with metadata for a project's downloadable files in Open Humans.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

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
                    csv_writer.writerow([
                        member_id, data_item['source'], data_item['basename'],
                        data_item['created']])


@click.command()
@click.option('-d', '--directory', help='Target directory', required=True)
@click.option('--create-csv', help='Create draft CSV metadata', required=True)
@click.option('--max-size', help='Maximum file size to consider.',
              default='128m', show_default=True)
@click.option('-v', '--verbose', help='Show INFO level logging', is_flag=True)
@click.option('--debug', help='Show DEBUG level logging.', is_flag=True)
def upload_metadata(directory, create_csv='', create_json='', review='',
             max_size='128m', verbose=False, debug=False):
    """
    Draft or review metadata files for uploading files to Open Humans.

    The target directory should either represent files for a single member (no
    subdirectories), or contain a subdirectory for each project member ID.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    max_bytes = parse_size(max_size)

    if create_csv:
        mk_metadata_csv(directory, create_csv, max_bytes=max_bytes)


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
def upload(directory, metadata_csv, master_token=None, member=None,
           access_token=None, safe=False, sync=False, max_size='128m',
           mode='default', verbose=False, debug=False):
    """
    Upload files for the project to Open Humans member accounts.

    If using a master access token and not specifying member ID:

    (1) Files should be organized in subdirectories according to project
    member ID, e.g.:

    \b
        main_directory/01234567/data.json
        main_directory/12345678/data.json
        main_directory/23456789/data.json

    (2) The metadata CSV should have the following format:

    \b
        1st column: Project member ID
        2nd column: filenames
        3rd & additional columns: Metadata fields (see below)

    \b
    If uploading for a specific member:
        (1) The local directory should not contain subdirectories.
        (2) The metadata CSV should have the following format:
            1st column: filenames
            2nd & additional columns: Metadata fields (see below)

    The default behavior is to overwrite files with matching filenames on
    Open Humans, but not otherwise delete files. (Use --safe or --sync to
    change this behavior.)

    \b
    If included, the following metadata columns should be correctly formatted:
        'tags': should be comma-separated strings
        'md5': should match the file's md5 hexdigest
        'creation_date', 'start_date', 'end_date': ISO 8601 dates or datetimes

    Other metedata fields (e.g. 'description') can be arbitrary strings.
    """
    if safe and sync:
        raise UsageError('Safe (--safe) and sync (--sync) modes are mutually '
                         'incompatible!')
    if not (master_token or access_token) or (master_token and access_token):
        raise UsageError('Please specify either a master access token (-T), '
                         'or an OAuth2 user access token (-t).')

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

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
