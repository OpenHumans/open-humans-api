import logging
import os

from humanfriendly import format_size, parse_size
import requests


MAX_FILE_DEFAULT = parse_size('128m')


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


def get_all_results(starting_page):
    """
    Given starting API query for Open Humans, iterate to get all results.
    """
    logging.info('Retrieving all results for {}'.format(starting_page))
    page = starting_page
    results = []

    while True:
        logging.debug('Getting data from: {}'.format(page))
        data = get_page(page)
        results = results + data['results']

        if data['next']:
            page = data['next']
        else:
            break

    return results


def download_file(download_url, target_filepath, max_bytes=MAX_FILE_DEFAULT):
    """
    Download a file.
    """
    response = requests.get(download_url, stream=True)
    size = int(response.headers['Content-Length'])

    if size > max_bytes:
        logging.info('Skipping {}, {} > {}'.format(
            target_filepath, format_size(size), format_size(max_bytes)))
        return

    logging.info('Downloading {} ({})'.format(
        target_filepath, format_size(size)))

    if os.path.exists(target_filepath):
        stat = os.stat(target_filepath)
        if stat.st_size == size:
            logging.info('Skipping, file exists and is the right '
                         'size: {}'.format(target_filepath))
            return
        else:
            logging.info('Replacing, file exists and is the wrong '
                         'size: {}'.format(target_filepath))
            os.remove(target_filepath)

    with open(target_filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    logging.info('Download complete: {}'.format(target_filepath))
