#!/usr/bin/env python

from setuptools import setup
import sys


def readme():
    with open('README.rst') as f:
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
    author='Madeleine Ball',
    author_email='support@openhumans.org',

    url='https://github.com/OpenHumans/open-humans-api',

    description='Tools for working with Open Humans APIs',
    long_description=readme(),

    version='0.1.2.2',

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
            'ohpub-download = ohapi.public:download',
            'ohproj-download = ohapi.command_line:download',
            'ohproj-download-metadata = ohapi.command_line:download_metadata',
            'ohproj-upload = ohapi.command_line:upload',
            'ohproj-upload-metadata = ohapi.command_line:upload_metadata',
        ]
    },

    install_requires=install_requires,
)
