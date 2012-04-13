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
    name='mfgames-writing',
    version='0.1.0.0',
    description='Utilities for text-base writing.',
    author='Dylan R. E. Moonfire',
    url='http://mfgames.com/mfgames-writing',
    scripts=[
        'src/mfgames-creole',
        'src/mfgames-docbook',
        'src/mfgames-ncx',
        'src/mfgames-opf',
        ],
    data_files=[
        ('share/mfgames-writing', [
            'lib/smartypants.py',
            ]),
        ('share/mfgames-writing/tools', [
            'src/tools/__init__.py',
            'src/tools/args.py',
            'src/tools/process.py',
            ]),
        ('share/mfgames-writing/writing', [
            'src/writing/__init__.py',
            'src/writing/constants.py',
            'src/writing/creole.py',
            'src/writing/format.py',
            ]),
        ('share/mfgames-writing/writing/docbook', [
            'src/writing/docbook/__init__.py',
            'src/writing/docbook/count.py',
            'src/writing/docbook/info.py',
            'src/writing/docbook/scan.py',
            'src/writing/docbook/text.py',
            ]),
        ('share/mfgames-writing/writing/ncx', [
            'src/writing/ncx/__init__.py',
            'src/writing/ncx/meta.py',
            'src/writing/ncx/author.py',
            'src/writing/ncx/title.py',
            'src/writing/ncx/nav.py',
            ]),
        ('share/mfgames-writing/writing/opf', [
            'src/writing/opf/__init__.py',
            'src/writing/opf/dc.py',
            'src/writing/opf/cover.py',
            'src/writing/opf/spine.py',
            'src/writing/opf/manifest.py',
            'src/writing/opf/uid.py',
            'src/writing/opf/toc.py',
            'src/writing/opf/guide.py',
            ]),
        ],
    )
