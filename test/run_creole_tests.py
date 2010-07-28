#!/usr/bin/python

#
# Imports
#

# System Imports
import hashlib
import imp
import os
import sys
import unittest

# Search Path
local_directory = os.path.normpath(os.path.dirname(__file__))
src_directory = os.path.realpath(local_directory + "/../src")

sys.path.append(src_directory)

# Internal Import
src_module = os.path.join(src_directory, 'mfgames-creole.py')

tool_code = open(src_module, 'rb')
tool = imp.load_source(
    hashlib.md5(src_module).hexdigest(),
    src_module,
    tool_code)

#
# Unit Test
#

class CreoleDocbookTests(unittest.TestCase):
    def run_tool(self, name, parameters):
        # Figure out the filenames of the input files.
        base_filename = os.path.join(local_directory, name)
        input_filename = base_filename + ".txt"
        expected_filename = name + ".expected"
        results_filename = name + ".xml"
        log_filename = name + ".log"

        # Add parameters to make the output as silent as possible.
        parameters.append('--log')
        parameters.append(log_filename)

        # Append the parameters for the output file and forcing it to
        # create the file, even if it exists.
        parameters.append("--force")
        parameters.append("-o")
        parameters.append(results_filename)
        parameters.append(input_filename)

        # Run the tool with the given parameters.
        #print(parameters)
        tool.do_creole_tool(parameters)

        # Load in the expected and resulting file.
        expected = open(expected_filename, 'rb')
        expected_contents = expected.read()
        expected.close()

        results = open(results_filename, 'rb')
        results_contents = results.read()
        results.close()

        # Assert that the contents of the file contents are the same.
        self.assertEqual(
            expected_contents,
            results_contents,
            "The contents of " + results_filename + " were not expected.")

        # Remove the run file and log.
        os.remove(results_filename)

        if os.path.exists(log_filename):
            os.remove(log_filename)

    def test_localwords(self):
        self.run_tool(
            'creole/creole_docbook_localwords',
            ['docbook', '--ignore-localwords'])

    def test_one_h1(self):
        self.run_tool(
            'creole/creole_docbook_one_h1',
            ['docbook'])

    def test_two_h1(self):
        self.run_tool(
            'creole/creole_docbook_two_h1',
            ['docbook'])

    def test_two_h2(self):
        self.run_tool(
            'creole/creole_docbook_two_h2',
            ['docbook'])

    def test_long_para(self):
        self.run_tool(
            'creole/creole_docbook_long_para',
            ['docbook'])

    def test_metadata_subjectset(self):
        self.run_tool(
            'creole/creole_docbook_metadata_subjectset',
            ['docbook', '--parse-metadata'])

    def test_metadata_subjectset_repeated(self):
        self.run_tool(
            'creole/creole_docbook_metadata_subjectset_repeated',
            ['docbook', '--parse-metadata'])

    def test_metadata_subjectset_interspersed(self):
        self.run_tool(
            'creole/creole_docbook_metadata_subjectset_interspersed',
            ['docbook', '--parse-metadata'])

    def test_quotes(self):
        self.run_tool(
            'creole/creole_docbook_quotes',
            ['docbook'])

#
# Entry
#

if __name__ == '__main__':
    unittest.main()
