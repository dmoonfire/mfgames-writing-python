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
import mfgames.docbook.text
import mfgames.process

#
# SAX Document Handler
#

class DocbookCreoleHandler(mfgames.docbook.text.DocbookHandler):
    def write_heading(self, depth, text):
        # Write out the section prefix
        self.output.write("=" * self.depth)
        self.output.write(' ')
            
        # Write out the title itself.
        self.output.write(self.wrap_buffer())
        self.output.write(os.linesep)

#
# Conversion Class
#

class DocbookCreoleConvertProcess(mfgames.docbook.text.DocbookTextConvertProcess):
    help = 'Converts Docbook 5 files into Creole.'
    log = logging.getLogger('creole')

    def get_extension(self):
        return "txt"

    def get_handler(self, args, output):
        return DocbookCreoleHandler(args, output)

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Docbook to Creole
        conversion.
        """

        # Add in the argument from the base class.
        super(DocbookCreoleConvertProcess, self).setup_arguments(parser)
