#!/usr/bin/env python

import logging
import os
import re
import signal

from functools import partial
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import click
import concurrent.futures
import requests
import sys

from humanfriendly import format_size, parse_size

from .api import get_page


BASE_URL = 'https://www.openhumans.org'
BASE_URL_API = '{}/api/public-data/'.format(BASE_URL)
LIMIT_DEFAULT = 100

def signal_handler_cb(signal_name, frame):
    """
    Exit on Ctrl-C.
    """
    os._exit(1)


def download_url(result, directory, max_bytes):
    """
    Download a file.

    :param result: This field contains a url from which data will be
        downloaded.
    :param directory: This field is the target directory to which data will be
        downloaded.
    :param max_bytes: This field is the maximum file size in bytes.
    """
    response = requests.get(result['download_url'], stream=True)

    # TODO: make this more robust by parsing the URL
    filename = response.url.split('/')[-1]
    filename = re.sub(r'\?.*$', '', filename)
    filename = '{}-{}'.format(result['user']['id'], filename)

    size = int(response.headers['Content-Length'])

    if size > max_bytes:
        logging.info('Skipping {}, {} > {}'.format(filename, format_size(size),
                                                   format_size(max_bytes)))

        return

    logging.info('Downloading {} ({})'.format(filename, format_size(size)))

    output_path = os.path.join(directory, filename)

    try:
        stat = os.stat(output_path)

        if stat.st_size == size:
            logging.info('Skipping "{}"; exists and is the right size'.format(
                filename))

            return
        else:
            logging.info('Removing "{}"; exists and is the wrong size'.format(
                filename))

            os.remove(output_path)
    except OSError:
        # TODO: check errno here?
        pass

    with open(output_path, 'wb') as f:
        total_length = response.headers.get('content-length')
        total_length = int(total_length)
        dl = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                dl += len(chunk)
                f.write(chunk)
                d = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]%d%s" % ('.' * d,
                                                   '' * (50 - d),
                                                   d * 2,
                                                   '%'))
                sys.stdout.flush
        print("\n")

    logging.info('Downloaded {}'.format(filename))


def download(source=None, username=None, directory='.', max_size='128m',
             quiet=None, debug=None):
    """
    Download public data from Open Humans.

    :param source: This field is the data source from which to download. It's
        default value is None.
    :param username: This fiels is username of user. It's default value is
        None.
    :param directory: This field is the target directory to which data is
        downloaded.
    :param max_size: This field is the maximum file size. It's default value is
        128m.
    :param quiet: This field is the logging level. It's default value is
        None.
    :param debug: This field is the logging level. It's default value is
        None.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.debug("Running with source: '{}'".format(source) +
                  " and username: '{}'".format(username) +
                  " and directory: '{}'".format(directory) +
                  " and max-size: '{}'".format(max_size))

    signal.signal(signal.SIGINT, signal_handler_cb)

    max_bytes = parse_size(max_size)

    options = {}

    if source:
        options['source'] = source

    if username:
        options['username'] = username

    page = '{}?{}'.format(BASE_URL_API, urlencode(options))

    results = []
    counter = 1

    logging.info('Retrieving metadata')

    while True:
        logging.info('Retrieving page {}'.format(counter))

        response = get_page(page)
        results = results + response['results']

        if response['next']:
            page = response['next']
        else:
            break

        counter += 1

    logging.info('Downloading {} files'.format(len(results)))

    download_url_partial = partial(download_url, directory=directory,
                                   max_bytes=max_bytes)

    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        for value in executor.map(download_url_partial, results):
            if value:
                logging.info(value)


def get_members_by_source(base_url=BASE_URL_API):
    """
    Function returns which members have joined each activity.

    :param base_url: It is URL: `https://www.openhumans.org/api/public-data`.
    """
    url = '{}members-by-source/'.format(base_url)
    response = get_page(url)
    return response


def get_sources_by_member(base_url=BASE_URL_API, limit=LIMIT_DEFAULT):
    """
    Function returns which activities each member has joined.

    :param base_url: It is URL: `https://www.openhumans.org/api/public-data`.
    :param limit: It is the limit of data send by one request.
    """
    url = '{}sources-by-member/'.format(base_url)
    page = '{}?{}'.format(url, urlencode({'limit': limit}))
    results = []
    while True:
        data = get_page(page)
        results = results + data['results']
        if data['next']:
            page = data['next']
        else:
            break
    return results
