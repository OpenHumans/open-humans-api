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


def signal_handler_cb(signal_name, frame):
    """
    Exit on Ctrl-C.
    """
    os._exit(1)


def download_url(result, directory, max_bytes):
    """
    Download a file.
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
def download(source, username, directory, max_size, quiet, debug):
    """
    Download public data from Open Humans.
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
