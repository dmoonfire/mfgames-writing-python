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

class DocbookCreoleHandler(writing.docbook.text.DocbookHandler):
    def write_heading(self, depth, text):
        # Write out the section depth prefix
        self.output.write("=" * self.depth)
        self.output.write(' ')
            
        # Write out the title itself and finish with a newline.
        self.output.write(self.wrap_buffer())
        self.output.write(os.linesep)

    def write_subjectsets(self, subjectsets):
        """
        Writes out the subject set data, as needed.
        """

        # Determine if we are formatting as a list.
        if self.args.subjectset_format == 'list':
            # Go through the dictionary as sorted keys.
            for schema in sorted(subjectsets.keys()):
                # Write out the beginning of the list.
                self.output.write("* ")
                self.output.write(schema)
                self.output.write(": ")
                self.output.write("; ".join(sorted(subjectsets[schema])))
                self.output.write(os.linesep)

        # Determine if we are formatting as dokuwiki tags.
        if self.args.subjectset_format == 'dokuwiki-tags':
            # Create a single list of all the tags at this point.
            tags = []

            for schema in subjectsets.keys():
                for term in subjectsets[schema]:
                    if term not in tags:
                        tags.append(term)

            # Create the dokuwiki tags.
            self.output.write("{{tag>")
            self.output.write(" ".join(sorted(tags)))
            self.output.write("}}")
            self.output.write(os.linesep)

#
# Conversion Class
#

class DocbookCreoleConvertProcess(
    writing.docbook.text.DocbookTextConvertProcess):
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

        # Add the Creole-conversion specific processes.
        parser.add_argument(
            '--subjectset-format',
            default='none',
            choices=['none', 'list', 'dokuwiki-tags'],
            type=str,
            help='Determines how subject sets are formatted.')
