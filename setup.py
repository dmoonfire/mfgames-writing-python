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
    version='0.0.0.0',
    description='Utilities for text-base writing.',
    author='D. Moonfire',
    url='http://mfgames.com/mfgames-writing',
    scripts=[
        'src/mfgames-creole',
        'src/mfgames-docbook',
        ],
    data_files=[
        ('share/mfgames-writing/writing', [
            'src/writing/__init__.py',
            'src/writing/constants.py',
            'src/writing/convert.py',
            'src/writing/process.py',
            ]),
        ('share/mfgames-writing/writing/creole', [
            'src/writing/creole/__init__.py',
            'src/writing/creole/docbook.py',
            ]),
        ('share/mfgames-writing/writing/docbook', [
            'src/writing/docbook/__init__.py',
            'src/writing/docbook/creole.py',
            'src/writing/docbook/text.py',
            ]),
        ],
    )
