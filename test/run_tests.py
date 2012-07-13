#!/usr/bin/env python

import os
import sys
import unittest

local_directory = os.path.normpath(os.path.dirname(__file__))
src_directory = os.path.realpath(local_directory + "/../src")

sys.path.insert(0, src_directory)

import mfgames_writing.type

#
# Entry
#

def run_tests():
    # Create the test loader that includes the individual test suites.
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames([
        'run_creole_tests',
        'run_type_tests',
        'run_docbook_tests'
    ])

    # Run all the combined tests in a single instance.
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
