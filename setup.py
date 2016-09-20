#!/usr/bin/env python

from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='open-humans-api',
    author='Madeleine Ball',
    author_email='support@openhumans.org',

    url='https://github.com/PersonalGenomesOrg/open-humans-api',

    description='Tools for working with Open Humans APIs',
    long_description=readme(),

    version='0.1.0',

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
            'ohproj-metadata = ohapi.command_line:metadata',
            'ohproj-upload = ohapi.command_line:upload',
        ]
    },

    install_requires=[
        'click>=6.3',
        'humanfriendly>=1.44.3',
        'requests>=2.9.1',
        'arrow>=0.8.0',
    ],
)
