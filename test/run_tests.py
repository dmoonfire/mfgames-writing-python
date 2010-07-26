#!/usr/bin/env python

#
# Imports
#

# System Imports
import unittest

#
# Entry
#

def run_tests():
    # Create the test loader that includes the individual test suites.
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames([
        'run_creole_tests',
        'run_docbook_tests'
    ])

    # Run all the combined tests in a single instance.
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
