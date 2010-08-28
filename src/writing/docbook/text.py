#
# Imports
#

# System Imports
import argparse
import codecs
import logging
import os
import re
import textwrap
import xml.sax

# Internal Imports
import writing.constants
import writing.convert
import writing.process

#
# Table of Contents
#

def is_structural(name):
    if name == "book":
        return True
    
    if name == "chapter":
        return True
    
    if name == "section":
        return True
    
    return False

class TableOfContents():
    def __init__(self):
        self.buffer = unicode()
        self.depth = 0
        self.id = None

class TableOfContentsHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.contents = []
        self.content = None
        self.depth = 0
        self.in_info = False

    def characters(self, contents):
        if self.in_info:
            self.content.buffer += contents

    def startElement(self, name, attrs):
        if name == "title":
            self.buffer = unicode()
            self.in_info = True

        if is_structural(name):
            self.depth = self.depth + 1
            self.content = TableOfContents()
            self.content.depth = self.depth
            self.contents.append(self.content)

            if attrs.has_key("id"):
                self.content.id = attrs["id"]

    def endElement(self, name):
        if name == "title":
            self.in_info = False

        if is_structural(name):
            self.depth = self.depth - 1

#
# Depth Handler
#

class ParsingContext():
    def __init__(self):
        self.depth = 0

#
# SAX Document Handler
#

class DocbookHandler(xml.sax.ContentHandler):
    # Flag used to determine if the parser is current going throguh an
    # <info> tag or a virtual <info> tag in the case of one is
    # missing.
    _subjectsets = dict()
    _subjectset_schema = ""

    def __init__(self, args, filename, output, contents):
        self.args = args
        self.contents = contents
        self.contents_index = 0
        self.buffer = ""
        self.depth = 0
        self.filename = filename
        self.need_toc = False

        # Keep track of the context
        self.context = ParsingContext()
        self.top_context = self.context
        self.context.output = output
        self.contexts = [self.context]

        if args.columns > 0:
            self.wrapper = textwrap.TextWrapper()
            self.wrapper.width = args.columns

    def characters(self, contents):
        self.buffer += contents

    def startElement(self, name, attrs):
        # Based on the name of the attribute determines what we do
        # with the character contents.
        if is_structural(name):
            # Check to see if we need to chunk the file and split into
            # a new file.
            if self.args.chunk > 0 and self.args.chunk == self.depth:
                self.start_chunk(name, attrs)

            self.depth = self.depth + 1
            self.context.depth = self.context.depth + 1
            self._in_info = True

            if self.depth > 2:
                self.context.output.write(os.linesep)

        if name == "quote":
            self.append_quote(True)

        if name == "simpara":
            self.context.output.write(os.linesep)

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

        if self.args.chunk > 0:
            self.top_context.output.write(os.linesep)

    def endElement(self, name):
        # Based on the attribute name determines how we close the elements.
        if is_structural(name):
            self.depth = self.depth - 1
            self.context.depth = self.context.depth - 1

            # Check to see if we need to close a chunked file.
            if self.args.chunk > 0 and self.args.chunk == self.depth:
                self.end_chunk(name)

        if name == "quote":
            self.append_quote(False)

        if name == "title":
            self.write_heading(self.depth, self.buffer)
            self.buffer = ""

        if name == "info":
            # Give the opportunity for the parser to write out the
            # subjectset information at the top of the section.
            self._write_subjectsets('section-top')

        if name == "simpara":
            self.context.output.write(self.wrap_buffer())
            self.context.output.write(os.linesep)
            self.buffer = ""

        if name == 'subjectterm':
            # Add the subject term to the given dictionary and clear
            # the buffer.
            self._subjectsets[self._subjectset_schema].append(self.buffer)
            self.buffer = ""

    def append_quote(self, opening):
        if self.args.quotes == 'simple':
            self.buffer += '"'
        if self.args.quotes == 'unicode':
            if opening:
                self.buffer += unichr(8220)
            else:
                self.buffer += unichr(8221)

    def start_chunk(self, name, attrs):
        # Figure out the name of the output file. This will be in the same
        # directory as the output file, but with a different filename.
        basename = attrs["id"]
        extname = os.path.splitext(self.filename)[1]
        dirname = os.path.dirname(self.filename)
        filename = os.path.join(dirname, basename + extname)

        # Create a new context and push it on the list.
        context = ParsingContext()
        context.output = codecs.open(filename, 'w', 'utf-8')
        self.contexts.append(context)
        self.context = context

    def end_chunk(self, name):
        # Close the current file we've opened.
        self.context.output.close()

        # Push the context up a level.
        self.context = self.contexts.pop()

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

class DocbookTextConvertProcess(writing.convert.ConvertProcess):
    help = 'Converts Docbook 5 files into text-based files.'
    log = logging.getLogger('creole')

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """

        # If we have chunking, then we need to only have one input file.
        if args.chunk > 0 and len(args.files) != 1:
            self.log.exception('The --chunk option can only be used with '
                + 'a single file.')
            return

        # Open the output stream.
        output = codecs.open(output_filename, 'w', 'utf-8')

        # Parse the XML to generate a table of contents.
        contentsHandler = TableOfContentsHandler()
        parser = xml.sax.make_parser()
        parser.setContentHandler(contentsHandler)
        parser.parse(open(input_filename))

        # Parse through the second time and actually generate the file.
        parser = xml.sax.make_parser()
        parser.setContentHandler(self.get_handler(
            args,
            output_filename,
            output,
            contentsHandler.contents))
        parser.parse(open(input_filename))

        # Close the output file.
        output.close()

    def get_handler(self, args, filename, output, contents):
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
            '--chunk',
            default=0,
            type=int,
            help="Setting this to higher than 0 will create "
                + "new files for sections.")
        parser.add_argument(
            '--columns',
            default=0,
            type=int,
            help="Sets the number of columns to wrap output.")
        parser.add_argument(
            '--quotes',
            default='simple',
            choices=['simple', 'unicode'],
            type=str,
            help="Determines how quotes are rendered.")
        parser.add_argument(
            '--subjectset-position',
            default='none',
            choices=['none', 'section-top', 'document-bottom'],
            type=str,
            help="Determines where subject sets will be rendered.")
