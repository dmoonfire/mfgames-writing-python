"""The various informational processes for reading a DocBook file and
producing output based on its contents."""


import os
import sys
import xml

import tools.process
import writing.docbook.scan


class ExtractSubjectsetsProcess(tools.process.InputFilesProcess):
    """Scans the DocBook file and extracts the subject sets."""

    def __init__(self):
        super(ExtractSubjectsetsProcess, self).__init__()

        self.args = None
        self.structure = None

    def get_help(self):
        """Returns the help string for the process."""
        return "Extracts subjectsets and terms from the input."

    def process(self, args):
        """Extracts the summaries from the given input files."""

        super(ExtractSubjectsetsProcess, self).process(args)

        self.args = args

        # Figure out the output, if we have one. If we are opening a file
        # then write out the BOM for Unicode.
        if args.output:
            output = codecs.open(
                args.output,
                'w',
                'utf-8')
            output.write(codecs.BOM_UTF8)
        else:
            output = sys.stdout

        # Go through all the input files.
        for filename in args.files:
            self.process_file(args, filename, output)

    def process_file(self, args, input_filename, output):
        """Converts the given file into Creole."""

        # Go through the file and build up the structural elements of
        # the document. This is used to determine chunking and file
        # generation.
        self.structure = writing.docbook.scan._StructureScanner(self, '')
        parser = xml.sax.make_parser()
        parser.setContentHandler(self.structure)
        parser.parse(open(input_filename))

        # Get all the subjects from the root element.
        subjectsets = {}
        self.structure.root_entry.get_subjectsets(subjectsets)

        # Check on the output format.
        if args.output_format == 'tsv':
            for subjectset in sorted(subjectsets.keys()):
                # We can have a None for the subject set, replace this with
                # blank.
                setname = subjectset

                if not subjectset:
                    setname = ''

                for subjectterm in sorted(subjectsets[subjectset]):
                    parts = [
                        input_filename,
                        setname,
                        subjectterm]
                    output.write('\t'.join(parts))
                    output.write(os.linesep)

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ExtractSubjectsetsProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--output',
            type=str,
            help="Output file otherwise use stdout.")
        parser.add_argument(
            '--output-format',
            default='tsv',
            choices=['tsv'],
            type=str,
            help="Lists the output format: tsv.")
        parser.add_argument(
            '--chunk-chapter',
            default='no',
            type=str,
            help="If not set to 'no', will chunk at chapters using the "
                + "value with substituting {id} and {number} in the string.")

