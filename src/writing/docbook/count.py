"""The various informational processes for reading a DocBook file and
producing output based on its contents."""


import os
import sys
import xml

import tools.process
import writing.docbook.scan
import writing.format

class _CountScanner(xml.sax.ContentHandler):
    """Parses the DocBook XML and counts the various elements."""

    def __init__(self, process):
        xml.sax.ContentHandler.__init__(self)

        self.process = process
        self.buffer = None
        self.gather_buffer = False
        self.context = None

    def characters(self, contents):
        """Processes character from the XML stream."""

        # If we are gathering characters into the buffer, then append
        # the contents.
        if self.gather_buffer:
            self.buffer += contents

    def startElement(self, name, attrs):
        """Processes the beginning of the XML element."""

        # When we start a paragraph, we want to gather all the text
        # into a buffer so we can process it.
        if name == "para" or name == "simpara" or name == "title":
            self.gather_buffer = True
            self.buffer = ""

    def endElement(self, name):
        """Processes the end of the XML element."""

        # At the end of each para or simppara tag, we increment the
        # paragraph counter and also process the collected buffer.
        if name == "para" or name == "simpara" or name == "title":
            # Indicate we are done gathering characters into the buffer.
            self.gather_buffer = False

            # Gather up the word count from the buffer. Passing None
            # into this will cause it to split on any whitespace.
            para_word_count = len(self.buffer.split(None))

            # Add the counts into the totals.
            self.process.counts["_total"][0] += 1
            self.process.counts["_total"][1] += para_word_count

            # Add the counts to the context, if we have one.
            if self.context:
                self.process.counts[self.context][0] += 1
                self.process.counts[self.context][1] += para_word_count

    def set_filename(self, filename):
        """Sets the filename as the context depending on the process
        options."""

        self.context = filename

        if not filename in self.process.counts:
            self.process.counts[filename] = [0, 0]
            self.process.order += [ filename ]

class CountProcess(tools.process.InputFilesProcess):
    """Scans the DocBook file and produces counts of various elements
    such as words, sentences, and paragraphs."""

    def __init__(self):
        # Have the parent class initialize itself.
        super(CountProcess, self).__init__()

        # Set up our member variables for processing.
        self.args = None

        # The counts is the critical part of this class. It is a
        # dictionary with the textual context as the key and an array
        # of numbers. The array consists of the counts in this order:
        # paragraph, word.
        self.counts = {
            "_title": ["Paras", "Words"],
            "_total": [0, 0]
            }

        # Keep track of the order scanned so we can order the output
        # appropriately.
        self.order = []

    def get_columns(self, key, value):
        """Gets and orders the columns for the output based on the
        given line (context) item."""

        # Pull out the record for the given key.
        record = self.counts[key]
        results = []

        # Go through the formats and add a column for each request.
        for format in self.args.format:
            if format.lower().startswith('w'):
                results.append(record[1])
            if format.lower().startswith('p'):
                results.append(record[0])
            if format.lower().startswith('c'):
                results.append(value)

        # Return the resulting table.
        return results

    def get_help(self):
        """Returns the help string for the process."""
        return "Counts various elements in the input."

    def process(self, args):
        # Save the arguments so the scanner can use them.
        self.args = args

        # Process the format column, which may contains strings,
        # commas, and other elements that need to be converted into a
        # list.
        formats = []

        if args.format:
            for format in args.format:
                for format_element in format.split(','):
                    formats.append(format_element)

        if len(formats) == 0:
            formats = ['paragraphs', 'words', 'context']

        args.format = formats

        # Process the files which in turn will call process_file on
        # each individual file.
        super(CountProcess, self).process(args)

        # Once the processing is done, we have to format the output to
        # the user. We do this by going through the dictionary and
        # adding up all the context elements into an array table that
        # will be later formatted to the user.

        # First check to see if we need headers.
        table = []

        if args.column_titles:
            table.append(self.get_columns("_title", "File"))

        # Second, go through all the contexts (but not the total).
        for context in self.order:
            table.append(self.get_columns(context, context))

        # Third, add the total column, if the arguments require it.
        if not args.no_total:
            table.append(self.get_columns("_total", "Total"))

        # Format and output the table to the standard out.
        writing.format.output_table(sys.stdout, table, args.thousands)

    def process_filename(self, filename):
        """Processes a single file and counts the appropriate
        elements."""

        # Set up the scanner and, optionally, the context as the file
        # being scanned.
        scanner = _CountScanner(self)
        scanner.set_filename(filename)

        # Open up the input file as XML and parse through the
        # contents. This will use the arguments to determine how to
        # break up the counts and produce a dictionary of the various
        # counts.
        parser = xml.sax.make_parser()
        parser.setContentHandler(scanner)
        parser.parse(open(filename))

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(CountProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--column-titles',
            '-c',
            action='store_true',
            help="Include the headers in the output.")
        parser.add_argument(
            '--thousands',
            action='store_true',
            help="Format the output with commas.")
        parser.add_argument(
            '--no-total',
            '-t',
            action='store_true',
            help="Do not include the total line in the output.")

        parser.add_argument(
            '--words',
            '-w',
            action='append_const',
            const='words',
            dest='format',
            help="Include the word count column.")
        parser.add_argument(
            '--paragraphs',
            '-p',
            action='append_const',
            const='paragraphs',
            dest='format',
            help="Include the paragraph count column.")
        parser.add_argument(
            '--format',
            '-f',
            action='append',
            dest='format',
            help="Include the paragraph count column.")
