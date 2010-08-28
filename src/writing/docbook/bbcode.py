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
import writing.constants
import writing.convert
import writing.docbook.text
import writing.process

#
# SAX Document Handler
#

class DocbookBBCodeHandler(writing.docbook.text.DocbookHandler):
    def write_heading(self, depth, text):
        # Write out the section depth prefix
        self.context.output.write("=" * self.depth)
        self.context.output.write(' ')
            
        # Write out the title itself and finish with a newline.
        self.context.output.write(text)
        self.context.output.write(os.linesep)

#
# Conversion Class
#

class DocbookBBCodeConvertProcess(
    writing.docbook.text.DocbookTextConvertProcess):
    help = 'Converts Docbook 5 files into BBCode.'
    log = logging.getLogger('bbcode')

    def get_extension(self):
        return "txt"

    def get_handler(self, args, filename, output, contents):
        return DocbookBBCodeHandler(args, filename, output, contents)

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Docbook to BBCode
        conversion.
        """

        # Add in the argument from the base class.
        super(DocbookBBCodeConvertProcess, self).setup_arguments(parser)
