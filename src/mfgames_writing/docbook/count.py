"""The various informational processes for reading a DocBook file and
producing output based on its contents."""


import mfgames_tools.process
import mfgames_writing.docbook.scan
import mfgames_writing.format
import os
import sys
import xml


class _CountScanner(xml.sax.ContentHandler):
    """Parses the DocBook XML and counts the various elements."""

    def __init__(self, process):
        xml.sax.ContentHandler.__init__(self)

        self.process = process
        self.buffer = None
        self.gather_buffer = False
        self.context = None
        self.need_chapter_title = False

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
        if name == "para" or name == "simpara":
            self.need_chapter_title = False
            self.gather_buffer = True
            self.buffer = ""

        if name == "title":
            self.gather_buffer = True
            self.buffer = ""

        if name == "chapter":
            self.set_chapter()
            

    def endElement(self, name):
        """Processes the end of the XML element."""

        # If we are at the end of the chapter, then clear the context
        # if we are chapter-based.
        if name == "chapter" and self.process.args.context == 'chapters':
            self.context = None

        # If we are at the end of a title, see if we think this is the
        # chapter title.
        if name == "title":
            self.gather_buffer = False

            if self.need_chapter_title:
                # We don't need the chapter title anymore
                self.need_chapter_title = False

                # Grab the current chapter name
                current_title = self.process.order[len(self.process.order) - 1]

                # Change both the counts and the order.
                self.process.counts[self.buffer] = (
                    self.process.counts[current_title])

                del self.process.counts[current_title]
                self.process.order[len(self.process.order) - 1] = self.buffer

                # Change the context for saving values.
                self.context = self.buffer

        # At the end of each para or simppara tag, we increment the
        # paragraph counter and also process the collected buffer.
        if name == "para" or name == "simpara" or name == "title":
            # Indicate we are done gathering characters into the buffer.
            self.gather_buffer = False

            # Gather up the word count from the buffer. Passing None
            # into this will cause it to split on any whitespace.
            para_word_count = len(self.buffer.split(None))

            # If we don't have a context, we don't do anything remarkable.
            if self.context:        
                # Add the counts into the totals.
                self.process.counts["_total"][0] += 1
                self.process.counts["_total"][1] += para_word_count

                # Add the counts to the context, if we have one.
                self.process.counts[self.context][0] += 1
                self.process.counts[self.context][1] += para_word_count

    def set_chapter(self):
        """Sets the chapter as the context depending on the process
        options."""

        if self.process.args.context != 'chapters':
            return

        self.context = 'Chapter ' + format(len(self.process.order) + 1)
        self.need_chapter_title = True

        if not self.context in self.process.counts:
            self.process.counts[self.context] = [0, 0]
            self.process.order.append(self.context)

    def set_filename(self, filename):
        """Sets the filename as the context depending on the process
        options."""

        if self.process.args.context != 'files':
            return

        self.context = filename

        if not filename in self.process.counts:
            self.process.counts[filename] = [0, 0]
            self.process.order.append(filename)


class CountProcess(mfgames_tools.process.InputFilesProcess):
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
            "_title": ["Paragraphs", "Words"],
            "_average": [0, 0],
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

        # Go through the columns and add a column for each request.
        for format in self.args.columns:
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
        columns = []

        if args.columns:
            for format in args.columns:
                for format_element in format.split(','):
                    columns.append(format_element)

        # If we don't have a defined format, then check to see if the
        # preset ones are requested.
        if len(columns) == 0:
            # -p and -w add a default setup, but only if we don't
            # already have one.
            if args.paragraphs:
                columns = ['paragraphs']

            if args.words:
                columns = ['words']

            # If we have either -p and/or -w, then we add context so
            # the output is similiar to the `wc` command.
            if len(columns) > 0:
                columns.append("context");

        # Check again to see if we didn't get anything.
        if len(columns) == 0:
            columns = ['paragraphs', 'words', 'context']

        args.columns = columns

        # Process the files which in turn will call process_file on
        # each individual file.
        super(CountProcess, self).process(args)

        # Once the processing is done, we have to format the output to
        # the user. We do this by going through the dictionary and
        # adding up all the context elements into an array table that
        # will be later formatted to the user.

        # First check to see if we need headers.
        table = []

        if args.headers:
            if args.context == 'files':
                table.append(self.get_columns("_title", "File"))
            if args.context == 'chapters':
                table.append(self.get_columns("_title", "Chapters"))

        # Second, go through all the contexts (but not the total).
        for context in self.order:
            table.append(self.get_columns(context, context))

        # Third, add the average row if the arguments request it.
        if args.average:
            count = len(self.order)

            if count > 0:
                self.counts["_average"][0] = int(self.counts["_total"][0] / count)
                self.counts["_average"][1] = int(self.counts["_total"][1] / count)
                table.append(self.get_columns("_average", "Average"))

        # Fourth, add the total column, if the arguments require it.
        if args.total:
            table.append(self.get_columns("_total", "Total"))

        # Format and output the table to the standard out.
        mfgames_writing.format.output_table(sys.stdout, table, args.format)

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
        parser.setFeature(
            "http://xml.org/sax/features/external-general-entities",
            False)
        parser.setContentHandler(scanner)
        parser.parse(open(filename))

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(CountProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--context',
            '-x',
            default='files',
            choices=['files', 'chapters'])
        parser.add_argument(
            '--total',
            default=False,
            action='store_true')
        parser.add_argument(
            '--average',
            default=False,
            action='store_true')
        parser.add_argument(
            '--headers',
            default=False,
            action='store_true')
        parser.add_argument(
            '--format',
            '-f',
            default=False,
            action='store_true')

        parser.add_argument(
            '--words',
            '-w',
            default=False,
            action='store_true',
            help="Include the word count column.")
        parser.add_argument(
            '--paragraphs',
            '-p',
            default=False,
            action='store_true',
            help="Include the paragraph count column.")
        parser.add_argument(
            '--columns',
            '-c',
            default=False,
            action='store_true',
            help="Include the paragraph count column.")
