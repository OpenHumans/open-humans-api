#!/usr/bin/env python

import os
import re
import signal

from functools import partial
from urllib import urlencode

import click
import concurrent.futures
import requests

from humanfriendly import format_size, parse_size

BASE_URL = 'https://www.openhumans.org'
BASE_URL_API = '{}/api/public-data/'.format(BASE_URL)


def signal_handler_cb(signal_name, frame):
    """
    Exit on Ctrl-C.
    """
    os._exit(1)


def get_page(url):
    """
    Get a single page of results.
    """
    response = requests.get(url)
    data = response.json()

    return data


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
        print 'Skipping {}, {} > {}'.format(filename, format_size(size),
                                            format_size(max_bytes))

        return

    print 'Downloading {} ({})'.format(filename, format_size(size))

    output_path = os.path.join(directory, filename)

    try:
        stat = os.stat(output_path)

        if stat.st_size == size:
            print 'Skipping "{}"; file exists and is the right size'.format(
                filename)

            return
        else:
            print 'Removing "{}"; file exists and is the wrong size'.format(
                filename)

            os.remove(output_path)
    except OSError:
        # TODO: check errno here?
        pass

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print 'Downloaded {}'.format(filename)


@click.command()
@click.option('-s', '--source', help='the source to download files from')
@click.option('-u', '--username', help='the user to download files from')
@click.option('-d', '--directory', help='the directory for downloaded files',
              default='.')
@click.option('-m', '--max-size', help='the maximum file size to download',
              default='128m')
def download(source, username, directory, max_size):
    """
    Download data from Open Humans.
    """
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

    print 'Retrieving metadata'

    while True:
        print 'Retrieving page {}'.format(counter)

        response = get_page(page)
        results = results + response['results']

        if response['next']:
            page = response['next']
        else:
            break

        counter += 1

    print 'Downloading {} files'.format(len(results))

    download_url_partial = partial(download_url, directory=directory,
                                   max_bytes=max_bytes)

    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        for value in executor.map(download_url_partial, results):
            if value:
                print value
