#!/usr/bin/env python

from setuptools import setup
import sys


def readme():
    with open('README.md') as f:
        return f.read()


# Add backport of futures unless Python version is 3.2 or later.
install_requires = [
    'click>=6.3',
    'humanfriendly>=1.44.3',
    'requests>=2.9.1',
    'arrow>=0.8.0',
]
if sys.version_info < (3, 2):
    install_requires.append('futures>=3.0.5')

setup(
    name='open-humans-api',
    author='Mad Price Ball',
    author_email='support@openhumans.org',

    url='https://github.com/OpenHumans/open-humans-api',

    description='Tools for working with Open Humans APIs',
    long_description=readme(),
    long_description_content_type="text/markdown",

    version='0.2.7',

    license='MIT',

    keywords=['open-humans'],

    classifiers=[
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],

    packages=['ohapi'],

    entry_points={
        'console_scripts': [
            'ohpub-download = ohapi.command_line:public_data_download_cli',
            'ohproj-download = ohapi.command_line:download_cli',
            'ohproj-download-metadata = ohapi.command_line:download_metadata_cli',
            'ohproj-upload = ohapi.command_line:upload_cli',
            'ohproj-upload-metadata = ohapi.command_line:upload_metadata_cli',
            'ohproj-oauth2-token-exchange = ohapi.command_line:oauth_token_exchange_cli',
            'ohproj-oauth2-url = ohapi.command_line:oauth2_auth_url_cli',
            'ohproj-message = ohapi.command_line:message_cli',
            'ohproj-delete = ohapi.command_line:delete_cli',
        ]
    },

    install_requires=install_requires,
)
