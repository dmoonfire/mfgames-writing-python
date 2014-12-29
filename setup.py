#!/usr/bin/env python

#
# Imports
#

# System Imports
from distutils.core import setup

#
# Setup
#

setup(
    # Metadata
    name='mfgames-writing',
    version='0.3.0.0',
    description='Utilities for manipulating and analyzing various writing-based formats.',
    author='Dylan R. E. Moonfire',
    author_email="contact@mfgames.com",
    url='http://mfgames.com/mfgames-writing',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Development Status :: 2 - Pre-Alpha",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Artistic Software",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Text Processing",
    ],

    # Scripts
    scripts=[
        'src/mfgames-creole',
        'src/mfgames-docbook',
        'src/mfgames-docbook-wordpress',
        'src/mfgames-markdown',
        'src/mfgames-ncx',
        'src/mfgames-opf',
        ],

    # Packages
    packages=[
        "mfgames_writing",
        "mfgames_writing.docbook",
        "mfgames_writing.markdown",
        "mfgames_writing.ncx",
        "mfgames_writing.opf",
        ],
    package_dir = {'': 'src'}
    )
