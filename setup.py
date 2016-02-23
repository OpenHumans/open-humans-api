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
    name='open-humans-downloader',
    author='Beau Gunderson',
    author_email='beau@personalgenomes.org',

    url='https://github.com/PersonalGenomesOrg/open-humans-downloader',

    description='Download public member data from Open Humans',
    long_description_markdown_filename='README.md',

    version='1.0.0',

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

    py_modules=['oh_download'],

    entry_points={
        'console_scripts': [
            'oh-download = oh_download:download',
        ]
    },

    install_requires=[
        'click>=6.3',
        'humanfriendly>=1.44.3',
        'requests>=2.9.1',
        'tomorrow>=0.2.4',
    ],

    setup_requires=setup_requires,
)
