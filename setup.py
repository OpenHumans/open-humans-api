#!/usr/bin/env python

import sys

from setuptools import setup

setup_requires = []

# I only release from OS X so markdown/pypandoc isn't needed in Windows
if not sys.platform.startswith('win'):
    setup_requires.extend([
        'setuptools-markdown',
    ])

setup(
    name='open-humans-api',
    author='Beau Gunderson, Madeleine Ball',
    author_email='support@openhumans.org',

    url='https://github.com/PersonalGenomesOrg/open-humans-api',

    description='Tools for working with Open Humans APIs',
    long_description_markdown_filename='README.md',

    version='0.1',

    license='MIT',

    keywords=['open-humans'],

    classifiers=[
        'Environment :: Console',
        'Development Status :: 4 - Beta',
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
            'ohpub-download = ohapi.public:download',
            'ohproj-download-all = ohapi.command_line:download_all',
            'ohproj-download-member = ohapi.command_line:download_member',
        ]
    },

    install_requires=[
        'click>=6.3',
        'humanfriendly>=1.44.3',
        'requests>=2.9.1',
        'arrow>=0.8.0',
    ],

    setup_requires=setup_requires,
)
