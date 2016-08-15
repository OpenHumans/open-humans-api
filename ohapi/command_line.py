import argparse
import logging

import click
from click import UsageError
from humanfriendly import parse_size
import requests

from .projects import OHProject

MAX_FILE_DEFAULT = parse_size('128m')


@click.command()
@click.option('-d', '--directory',
              help='Target directory for downloaded files.', required=True)
@click.option('-T', '--master-token', help='Project master access token.',
              required=True)
@click.option('-m', '--max-size', help='Maximum file size to download.',
              default='128m', show_default=True)
@click.option('-v', '--verbose', help='Report INFO level logging to stdout',
              is_flag=True)
@click.option('-debug', help='Report DEBUG level logging to stdout.',
              is_flag=True)
def download_all(directory, master_token, max_size='128m',
                 verbose=False, debug=False):
    """
    Download files for all project members to the target directory.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    project = OHProject(master_access_token=master_token)
    project.download_to_dir(target_dir=directory, all_members=True)


@click.command()
@click.option('-d', '--directory', help='Target directory for downloaded files.', required=True)
@click.option('-T', '--master-token', help='Project master access token.')
@click.option('-m', '--member', help='Project member ID.')
@click.option('-t', '--access-token', help='OAuth2 user access token.')
@click.option('-m', '--max-size', help='Maximum file size to download.',
              default='128m', show_default=True)
@click.option('-v', '--verbose', help='Report INFO level logging to stdout', is_flag=True)
@click.option('-debug', help='Report DEBUG level logging to stdout.', is_flag=True)
def download_member(directory, master_token=None, member=None, access_token=None, max_size='128m', verbose=False, debug=False):
    """
    Download files for a specific member to the target directory.

    This command either accepts an OAuth2 user token (-t), or a master access
    token (-T) and project member ID (-m).
    """
    if not (master_token or access_token):
        raise UsageError('Please specify either a master access token (-T), or an '
                         'OAuth2 user access token (-t).')
    elif (master_token and access_token):
        raise UsageError('Only specify one type of token (-t or -T), not both.')
    elif (master_token and not member):
        raise UsageError('Project member ID (-m) must be specified if using a '
                         'master access token (-T).')
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    if master_token and member:
        project = OHProject(master_access_token=master_token)
        project.download_to_dir(
            target_dir=directory, project_member=member, max_size=max_size)
    elif access_token:
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
               'exchange-member/?access_token={}'.format(access_token))
        req = requests.get(url)
        logging.info('request completed')
        member_data = req.json()
        logging.info('JSON parsed')
        OHProject.download_member_to_dir(member_data=member_data,
                                         target_member_dir=directory,
                                         max_size=max_size)
