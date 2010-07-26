#
# Imports
#

# System Imports
import argparse
import logging
import os
import textwrap
import xml.sax

# Internal Imports
import mfgames.constants
import mfgames.convert
import mfgames.process

#
# SAX Document Handler
#

class DocbookCreoleHandler(xml.sax.ContentHandler):
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
            # Write out the section prefix
            self.output.write("=" * self.depth)
            self.output.write(' ')
            
            # Write out the title itself.
            self.output.write(self.wrap_buffer())
            self.output.write(os.linesep)

            # Clear the buffer for the next paragraph.
            self.buffer = ""

        if name == "simpara":
            self.output.write(self.wrap_buffer())
            self.output.write(os.linesep)
            self.buffer = ""

    def wrap_buffer(self):
        if self.args.columns > 0:
            results = self.wrapper.fill(self.buffer)
            return results

        return self.buffer

#
# Conversion Class
#

class DocbookCreoleConvertProcess(mfgames.convert.ConvertProcess):
    help = 'Converts Docbook 5 files into Creole.'
    log = logging.getLogger('creole')

    def get_extension(self):
        return "txt"

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """

        # Open the output stream.
        output = open(output_filename, 'w')

        # Open an SAX XML stream for the DocBook contents.
        parser = xml.sax.make_parser()
        parser.setContentHandler(DocbookCreoleHandler(args, output))
        parser.parse(open(input_filename))

        # Close the output file.
        output.close()

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Docbook to Creole
        conversion.
        """

        # Add in the argument from the base class.
        super(DocbookCreoleConvertProcess, self).setup_arguments(parser)

        # Add in the Creole-specific generations.
        parser.add_argument(
            '--columns',
            default=0,
            type=int,
            help="Sets the number of columns to wrap outout.")
