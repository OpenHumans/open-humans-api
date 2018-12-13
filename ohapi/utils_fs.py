"""
Utility functions to sync and work with Open Humans data in a local filesystem.
"""
import csv
import hashlib
import logging
import os
import re

import arrow
from humanfriendly import format_size, parse_size
from .api import _exceeds_size
import requests


MAX_FILE_DEFAULT = parse_size('128m')


def strip_zip_suffix(filename):
    """
    Helper function to strip suffix from filename.

    :param filename: This field is the name of file.
    """
    if filename.endswith('.gz'):
        return filename[:-3]
    elif filename.endswith('.bz2'):
        return filename[:-4]
    else:
        return filename


def guess_tags(filename):
    """
    Function to get potential tags for files using the file names.

    :param filename: This field is the name of file.
    """
    tags = []
    stripped_filename = strip_zip_suffix(filename)
    if stripped_filename.endswith('.vcf'):
        tags.append('vcf')
    if stripped_filename.endswith('.json'):
        tags.append('json')
    if stripped_filename.endswith('.csv'):
        tags.append('csv')
    return tags


def characterize_local_files(filedir, max_bytes=MAX_FILE_DEFAULT):
    """
    Collate local file info as preperation for Open Humans upload.

    Note: Files with filesize > max_bytes are not included in returned info.

    :param filedir: This field is target directory to get files from.
    :param max_bytes: This field is the maximum file size to consider. Its
        default value is 128m.
    """
    file_data = {}
    logging.info('Characterizing files in {}'.format(filedir))
    for filename in os.listdir(filedir):
        filepath = os.path.join(filedir, filename)
        file_stats = os.stat(filepath)
        creation_date = arrow.get(file_stats.st_ctime).isoformat()
        file_size = file_stats.st_size
        if file_size <= max_bytes:
            file_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    file_md5.update(chunk)
            md5 = file_md5.hexdigest()
            file_data[filename] = {
                'tags': guess_tags(filename),
                'description': '',
                'md5': md5,
                'creation_date': creation_date,
            }
    return file_data


def validate_metadata(target_dir, metadata):
    """
    Check that the files listed in metadata exactly match files in target dir.

    :param target_dir: This field is the target directory from which to
        match metadata
    :param metadata: This field contains the metadata to be matched.
    """
    if not os.path.isdir(target_dir):
        print("Error: " + target_dir + " is not a directory")
        return False
    file_list = os.listdir(target_dir)
    for filename in file_list:
        if filename not in metadata:
            print("Error: " + filename + " present at" + target_dir +
                  " not found in metadata file")
            return False
    for filename in metadata:
        if filename not in file_list:
            print("Error: " + filename + " present in metadata file " +
                  " not found on disk at: " + target_dir)
            return False
    return True


def load_metadata_csv_single_user(csv_in, header, tags_idx):
    """
    Return the metadata as requested for a single user.

    :param csv_in: This field is the csv file to return metadata from.
    :param header: This field contains the headers in the csv file
    :param tags_idx: This field contains the index of the tags in the csv
        file.
    """
    metadata = {}
    n_headers = len(header)
    for index, row in enumerate(csv_in, 2):
        if row[0] == "":
            raise ValueError('Error: In row number ' + str(index) + ':' +
                             ' "filename" must not be empty.')
        if row[0] == 'None' and [x == 'NA' for x in row[1:]]:
            break
        if len(row) != n_headers:
            raise ValueError('Error: In row number ' + str(index) + ':' +
                             ' Number of columns (' + str(len(row)) +
                             ') doesnt match Number of headings (' +
                             str(n_headers) + ')')
        metadata[row[0]] = {
            header[i]: row[i] for i in range(1, len(header)) if
            i != tags_idx
        }
        metadata[row[0]]['tags'] = [t.strip() for t in
                                    row[tags_idx].split(',') if
                                    t.strip()]
    return metadata


def load_metadata_csv_multi_user(csv_in, header, tags_idx):
    """
    Return the metadata as requested for multiple users.

    :param csv_in: This field is the csv file to return metadata from.
    :param header: This field contains the headers in the csv file
    :param tags_idx: This field contains the index of the tags in the csv
        file.
    """
    metadata = {}
    n_headers = len(header)
    for index, row in enumerate(csv_in, 2):
        if row[0] == "":
            raise ValueError('Error: In row number ' + str(index) + ':' +
                             ' "project_member_id" must not be empty.')
        if row[1] == "":
            raise ValueError('Error: In row number ' + str(index) + ':' +
                             ' "filename" must not be empty.')
        if row[0] not in metadata:
            metadata[row[0]] = {}
        if row[1] == 'None' and all([x == 'NA' for x in row[2:]]):
            continue
        if len(row) != n_headers:
            raise ValueError('Error: In row number ' + str(index) + ':' +
                             ' Number of columns (' + str(len(row)) +
                             ') doesnt match Number of headings (' +
                             str(n_headers) + ')')
        metadata[row[0]][row[1]] = {
            header[i]: row[i] for i in range(2, len(header)) if
            i != tags_idx
        }
        metadata[row[0]][row[1]]['tags'] = [t.strip() for t in
                                            row[tags_idx].split(',') if
                                            t.strip()]
    return metadata


def load_metadata_csv(input_filepath):
    """
    Return dict of metadata.

    Format is either dict (filenames are keys) or dict-of-dicts (project member
    IDs as top level keys, then filenames as keys).

    :param input_filepath: This field is the filepath of the csv file.
    """
    with open(input_filepath) as f:
        csv_in = csv.reader(f)
        header = next(csv_in)
        if 'tags' in header:
            tags_idx = header.index('tags')
        else:
            raise ValueError('"tags" is a compulsory column in metadata file.')
        if header[0] == 'project_member_id':
            if header[1] == 'filename':
                metadata = load_metadata_csv_multi_user(csv_in, header,
                                                        tags_idx)
            else:
                raise ValueError('The second column must be "filename"')
        elif header[0] == 'filename':
            metadata = load_metadata_csv_single_user(csv_in, header, tags_idx)
        else:
            raise ValueError('Incorrect Formatting of metadata. The first' +
                             ' column for single user upload should be' +
                             ' "filename". For multiuser uploads the first ' +
                             'column should be "project member id" and the' +
                             ' second column should be "filename"')
    return metadata


def print_error(e):
    """
    Helper function to print error.

    :param e: This field is the error to be printed.
    """
    print(" ".join([str(arg) for arg in e.args]))


def validate_date(date, project_member_id, filename):
    """
    Check if date is in ISO 8601 format.

    :param date: This field is the date to be checked.
    :param project_member_id: This field is the project_member_id corresponding
        to the date provided.
    :param filename: This field is the filename corresponding to the date
        provided.
    """
    try:
        arrow.get(date)
    except Exception:
        return False
    return True


def is_single_file_metadata_valid(file_metadata, project_member_id, filename):
    """
    Check if metadata fields like project member id, description, tags, md5 and
    creation date are valid for a single file.

    :param file_metadata: This field is metadata of file.
    :param project_member_id: This field is the project member id corresponding
        to the file metadata provided.
    :param filename: This field is the filename corresponding to the file
        metadata provided.
    """
    if project_member_id is not None:
        if not project_member_id.isdigit() or len(project_member_id) != 8:
            raise ValueError(
                'Error: for project member id: ', project_member_id,
                ' and filename: ', filename,
                ' project member id must be of 8 digits from 0 to 9')
    if 'description' not in file_metadata:
        raise ValueError(
            'Error: for project member id: ', project_member_id,
            ' and filename: ', filename,
            ' "description" is a required field of the metadata')

    if not isinstance(file_metadata['description'], str):
        raise ValueError(
            'Error: for project member id: ', project_member_id,
            ' and filename: ', filename,
            ' "description" must be a string')

    if 'tags' not in file_metadata:
        raise ValueError(
            'Error: for project member id: ', project_member_id,
            ' and filename: ', filename,
            ' "tags" is a required field of the metadata')

    if not isinstance(file_metadata['tags'], list):
        raise ValueError(
            'Error: for project member id: ', project_member_id,
            ' and filename: ', filename,
            ' "tags" must be an array of strings')

    if 'creation_date' in file_metadata:
        if not validate_date(file_metadata['creation_date'], project_member_id,
                             filename):
            raise ValueError(
                'Error: for project member id: ', project_member_id,
                ' and filename: ', filename,
                ' Dates must be in ISO 8601 format')

    if 'md5' in file_metadata:
        if not re.match(r'[a-f0-9]{32}$', file_metadata['md5'],
                        flags=re.IGNORECASE):
            raise ValueError(
                'Error: for project member id: ', project_member_id,
                ' and filename: ', filename,
                ' Invalid MD5 specified')

    return True


def review_metadata_csv_single_user(filedir, metadata, csv_in, n_headers):
    """
    Check validity of metadata for single user.

    :param filedir: This field is the filepath of the directory whose csv
        has to be made.
    :param metadata: This field is the metadata generated from the
        load_metadata_csv function.
    :param csv_in: This field returns a reader object which iterates over the
        csv.
    :param n_headers: This field is the number of headers in the csv.
    """
    try:
        if not validate_metadata(filedir, metadata):
            return False
        for filename, file_metadata in metadata.items():
            is_single_file_metadata_valid(file_metadata, None, filename)
    except ValueError as e:
        print_error(e)
        return False
    return True


def validate_subfolders(filedir, metadata):
    """
    Check that all folders in the given directory have a corresponding
    entry in the metadata file, and vice versa.

    :param filedir: This field is the target directory from which to
        match metadata
    :param metadata: This field contains the metadata to be matched.
    """
    if not os.path.isdir(filedir):
        print("Error: " + filedir + " is not a directory")
        return False
    subfolders = os.listdir(filedir)
    for subfolder in subfolders:
        if subfolder not in metadata:
            print("Error: folder " + subfolder +
                  " present on disk but not in metadata")
            return False
    for subfolder in metadata:
        if subfolder not in subfolders:
            print("Error: folder " + subfolder +
                  " present in metadata but not on disk")
            return False
    return True


def review_metadata_csv_multi_user(filedir, metadata, csv_in, n_headers):
    """
    Check validity of metadata for multi user.

    :param filedir: This field is the filepath of the directory whose csv
        has to be made.
    :param metadata: This field is the metadata generated from the
        load_metadata_csv function.
    :param csv_in: This field returns a reader object which iterates over the
        csv.
    :param n_headers: This field is the number of headers in the csv.
    """
    try:
        if not validate_subfolders(filedir, metadata):
            return False
        for project_member_id, member_metadata in metadata.items():
            if not validate_metadata(os.path.join
                                     (filedir, project_member_id),
                                     member_metadata):
                return False
            for filename, file_metadata in member_metadata.items():
                is_single_file_metadata_valid(file_metadata, project_member_id,
                                              filename)

    except ValueError as e:
        print_error(e)
        return False
    return True


def review_metadata_csv(filedir, input_filepath):
    """
    Check validity of metadata fields.

    :param filedir: This field is the filepath of the directory whose csv
        has to be made.
    :param outputfilepath: This field is the file path of the output csv.
    :param max_bytes: This field is the maximum file size to consider. Its
        default value is 128m.
    """
    try:
        metadata = load_metadata_csv(input_filepath)
    except ValueError as e:
        print_error(e)
        return False

    with open(input_filepath) as f:
        csv_in = csv.reader(f)
        header = next(csv_in)
        n_headers = len(header)
        if header[0] == 'filename':
            res = review_metadata_csv_single_user(filedir, metadata,
                                                  csv_in, n_headers)
            return res
        if header[0] == 'project_member_id':
            res = review_metadata_csv_multi_user(filedir, metadata,
                                                 csv_in, n_headers)
            return res


def write_metadata_to_filestream(filedir, filestream,
                                 max_bytes=MAX_FILE_DEFAULT):
    """
    Make metadata file for all files in a directory(helper function)

    :param filedir: This field is the filepath of the directory whose csv
        has to be made.
    :param filestream: This field is a stream for writing to the csv.
    :param max_bytes: This field is the maximum file size to consider. Its
        default value is 128m.
    """
    csv_out = csv.writer(filestream)
    subdirs = [os.path.join(filedir, i) for i in os.listdir(filedir) if
               os.path.isdir(os.path.join(filedir, i))]
    if subdirs:
        logging.info('Making metadata for subdirs of {}'.format(filedir))
        if not all([re.match('^[0-9]{8}$', os.path.basename(d))
                    for d in subdirs]):
            raise ValueError("Subdirs not all project member ID format!")
        csv_out.writerow(['project_member_id', 'filename', 'tags',
                          'description', 'md5', 'creation_date'])
        for subdir in subdirs:
            file_info = characterize_local_files(
                filedir=subdir, max_bytes=max_bytes)
            proj_member_id = os.path.basename(subdir)
            if not file_info:
                csv_out.writerow([proj_member_id, 'None',
                                  'NA', 'NA', 'NA', 'NA'])
                continue
            for filename in file_info:
                csv_out.writerow([proj_member_id,
                                  filename,
                                  ', '.join(file_info[filename]['tags']),
                                  file_info[filename]['description'],
                                  file_info[filename]['md5'],
                                  file_info[filename]['creation_date'],
                                  ])
    else:
        csv_out.writerow(['filename', 'tags',
                          'description', 'md5', 'creation_date'])
        file_info = characterize_local_files(
            filedir=filedir, max_bytes=max_bytes)
        for filename in file_info:
            csv_out.writerow([filename,
                              ', '.join(file_info[filename]['tags']),
                              file_info[filename]['description'],
                              file_info[filename]['md5'],
                              file_info[filename]['creation_date'],
                              ])


def mk_metadata_csv(filedir, outputfilepath, max_bytes=MAX_FILE_DEFAULT):
    """
    Make metadata file for all files in a directory.

    :param filedir: This field is the filepath of the directory whose csv
        has to be made.
    :param outputfilepath: This field is the file path of the output csv.
    :param max_bytes: This field is the maximum file size to consider. Its
        default value is 128m.
    """
    with open(outputfilepath, 'w') as filestream:
        write_metadata_to_filestream(filedir, filestream, max_bytes)


def download_file(download_url, target_filepath, max_bytes=MAX_FILE_DEFAULT):
    """
    Download a file.

    :param download_url: This field is the url from which data will be
        downloaded.
    :param target_filepath: This field is the path of the file where
        data will be downloaded.
    :param max_bytes: This field is the maximum file size to download. Its
        default value is 128m.
    """
    response = requests.get(download_url, stream=True)
    size = int(response.headers['Content-Length'])

    if _exceeds_size(size, max_bytes, target_filepath) is True:
        return response

    logging.info('Downloading {} ({})'.format(
        target_filepath, format_size(size)))

    if os.path.exists(target_filepath):
        stat = os.stat(target_filepath)
        if stat.st_size == size:
            logging.info('Skipping, file exists and is the right '
                         'size: {}'.format(target_filepath))
            return response
        else:
            logging.info('Replacing, file exists and is the wrong '
                         'size: {}'.format(target_filepath))
            os.remove(target_filepath)

    with open(target_filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    logging.info('Download complete: {}'.format(target_filepath))
    return response


def read_id_list(filepath):
    """
    Get project member id from a file.

    :param filepath: This field is the path of file to read.
    """
    if not filepath:
        return None
    id_list = []
    with open(filepath) as f:
        for line in f:
            line = line.rstrip()
            if not re.match('^[0-9]{8}$', line):
                raise('Each line in whitelist or blacklist is expected '
                      'to contain an eight digit ID, and nothing else.')
            else:
                id_list.append(line)
    return id_list
