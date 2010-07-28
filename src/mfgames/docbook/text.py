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

        if name == "section":
            self.depth = self.depth + 1
            self.output.write(os.linesep)

        if name == "simpara":
            self.output.write(os.linesep)

    def endElement(self, name):
        # Based on the attribute name determines how we close the elements.
        if name == "section":
            self.depth = self.depth - 1

        if name == "title":
            self.write_heading(self.depth, self.buffer)
            self.buffer = ""

        if name == "simpara":
            self.output.write(self.wrap_buffer())
            self.output.write(os.linesep)
            self.buffer = ""

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

    def write_heading(self, depth, text):
        """
        Writes out a heading string.
        """

        raise Exception("Derived class does not extend write_heading()")

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

        # Add in the Creole-specific generations.
        parser.add_argument(
            '--columns',
            default=0,
            type=int,
            help="Sets the number of columns to wrap output.")
