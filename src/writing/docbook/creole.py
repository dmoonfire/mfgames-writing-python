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
        # If we have a depth, add a newline.
        if self.depth > 1:
            self.context.output.write(os.linesep)

        # Write out the section depth prefix
        self.context.output.write("=" * self.context.depth)
        self.context.output.write(' ')
            
        # Write out the title itself and finish with a newline.
        self.context.output.write(text)
        self.context.output.write(os.linesep)

        # Write out the TOC if we are chunking.
        if self.args.chunk == self.depth - 1:
            for content in self.contents:
                if content.buffer == text:
                    self.top_context.output.write(os.linesep)
                    self.top_context.output.write(
                        "* [[" + content.id + "|" + text + "]]")

    def write_subjectsets(self, subjectsets):
        """
        Writes out the subject set data, as needed.
        """

        # Determine if we are formatting as a list.
        if self.args.subjectset_format == 'list':
            # Go through the dictionary as sorted keys.
            for schema in sorted(subjectsets.keys()):
                # Write out the beginning of the list.
                self.context.output.write("* ")
                self.context.output.write(schema)
                self.context.output.write(": ")
                self.context.output.write(
                    "; ".join(sorted(subjectsets[schema])))
                self.context.output.write(os.linesep)

        # Determine if we are formatting as dokuwiki tags.
        if self.args.subjectset_format == 'dokuwiki-tags':
            # Create a single list of all the tags at this point.
            tags = []

            for schema in subjectsets.keys():
                for term in subjectsets[schema]:
                    if term not in tags:
                        tags.append(term)

            # Create the dokuwiki tags.
            self.context.output.write("{{tag>")
            self.context.output.write(" ".join(sorted(tags)))
            self.context.output.write("}}")
            self.context.output.write(os.linesep)

#
# Conversion Class
#

class DocbookCreoleConvertProcess(
    writing.docbook.text.DocbookTextConvertProcess):
    help = 'Converts Docbook 5 files into Creole.'
    log = logging.getLogger('creole')

    def get_extension(self):
        return "txt"

    def get_handler(self, args, filename, output, contents):
        return DocbookCreoleHandler(args, filename, output, contents)

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
