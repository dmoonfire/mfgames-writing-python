#
# Imports
#

# System Imports
import argparse
import logging
import os
import re
import textwrap
import xml.sax

# Internal Imports
import mfgames.constants
import mfgames.convert
import mfgames.process

#
# SAX Document Handler
#

class DocbookHandler(xml.sax.ContentHandler):
    # Flag used to determine if the parser is current going throguh an
    # <info> tag or a virtual <info> tag in the case of one is
    # missing.
    _subjectsets = dict()
    _subjectset_schema = ""

    def __init__(self, args, output):
        self.args = args
        self.output = output
        self.buffer = ""
        self.depth = 0

        if args.columns > 0:
            self.wrapper = textwrap.TextWrapper()
            self.wrapper.width = args.columns

    def characters(self, contents):
        self.buffer += contents

    def startElement(self, name, attrs):
        # Based on the name of the attribute determines what we do
        # with the character contents.
        if name == "article":
            self.depth = 1
            self._in_info = True

        if name == "section":
            self.depth = self.depth + 1
            self.output.write(os.linesep)
            self._in_info = True

        if name == "simpara":
            self.output.write(os.linesep)

            # Give the opportunity for the parser to write out the
            # subjectset information at the top of the section.
            self._write_subjectsets('section-top')

        if name == 'subjectset':
            # Keep track of the current schema and make sure there is
            # a dictionary key for that schema.
            self._subjectset_schema = attrs['schema']

            if self._subjectset_schema not in self._subjectsets:
                self._subjectsets[self._subjectset_schema] = [];

    def endDocument(self):
        # If the subjectset position is set at the bottom, give the
        # opportunity to write out the tags there.
        self._write_subjectsets('document-bottom')

    def endElement(self, name):
        # Based on the attribute name determines how we close the elements.
        if name == "section":
            self.depth = self.depth - 1

        if name == "title":
            self.write_heading(self.depth, self.buffer)
            self.buffer = ""

        if name == "info":
            # Give the opportunity for the parser to write out the
            # subjectset information at the top of the section.
            self._write_subjectsets('section-top')

        if name == "simpara":
            self.output.write(self.wrap_buffer())
            self.output.write(os.linesep)
            self.buffer = ""

        if name == 'subjectterm':
            # Add the subject term to the given dictionary and clear
            # the buffer.
            self._subjectsets[self._subjectset_schema].append(self.buffer)
            self.buffer = ''

    def wrap_buffer(self):
        # Pull out the buffer and clean up the results, removing extra
        # whitespace and filling to the given columns.
        results = self.buffer
        results = results.strip()
        results = re.sub(r'\s+', ' ', results)
        results = re.sub(r'\s+', ' ', results, re.MULTILINE)

        if self.args.columns > 0:
            results = self.wrapper.fill(results)

        return results

    def _write_subjectsets(self, position):
        """
        Determines if the subject set should be written out and
        cleared. The position given (e.g., section-top,
        document-bottom) will match the position given in the
        arguments.
        """

        # If we don't have any subject sets, then don't bother doing
        # anything.
        if len(self._subjectsets) == 0:
            return

        # Check the position given and see if it matches the position
        # given in the arguments. If they don't match, then we won't
        # be writing out the subjectsets.
        if position != self.args.subjectset_position:
            return

        # We are in the right position and we have at least one parsed
        # subject set, so allow the derived parser to generate it.
        self.write_subjectsets(self._subjectsets)

        # Clear out the subjectsets.
        self._subjectsets = dict()

    def write_heading(self, depth, text):
        """
        Writes out a heading string.
        """

        raise Exception("Derived class does not extend write_heading()")

    def write_subjectsets(self, subjectsets):
        """
        Writes out the subjectsets from the parser in any format that
        is appropriate. The derived format is dependent on the parser.
        """

        return

#
# Conversion Class
#

class DocbookTextConvertProcess(mfgames.convert.ConvertProcess):
    help = 'Converts Docbook 5 files into text-based files.'
    log = logging.getLogger('creole')

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """

        # Open the output stream.
        output = open(output_filename, 'w')

        # Open an SAX XML stream for the DocBook contents.
        parser = xml.sax.make_parser()
        parser.setContentHandler(self.get_handler(args, output))
        parser.parse(open(input_filename))

        # Close the output file.
        output.close()

    def get_handler(self, args, output):
        """
        Gets a SAX handler for the given arguments and output.
        """

        raise Exception('Derived class did not extend get_handler()')

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Docbook text
        conversions.
        """

        # Add in the argument from the base class.
        super(DocbookTextConvertProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--columns',
            default=0,
            type=int,
            help="Sets the number of columns to wrap output.")
        parser.add_argument(
            '--subjectset-position',
            default='none',
            choices=['none', 'section-top', 'document-bottom'],
            type=str,
            help="Determines where subject sets will be rendered.")
