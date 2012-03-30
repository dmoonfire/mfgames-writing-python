"""The various informational processes for reading a DocBook file and
producing output based on its contents."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class ListManifestProcess(tools.process.InputFileProcess):
    """Scans the OPF file and lists the manifest entries."""

    def __init__(self):
        super(ListManifestProcess, self).__init__()

        self.args = None
        self.structure = None

    def get_help(self):
        """Returns the help string for the process."""
        return "Lists the manifests of a OPF."

    def process(self, args):
        """Perform the list manifest process."""

        super(ListManifestProcess, self).process(args)

        self.args = args

        # Create a SAX parser to go through the file looking for
        # manifest entries.
        opf = writing.opf.Opf()
        scanner = writing.opf._OpfScanner(opf)
        parser = xml.sax.make_parser()
        parser.setContentHandler(scanner)
        parser.parse(open(args.file))

        # Display the results in the appropriate format.
        if args.format == 'tsv':
            for manifest_id in sorted(opf.manifest_items.keys()):
                # Pull out the manifest.
                manifest = opf.manifest_items[manifest_id]

                # Write it out.
                parts = [
                    manifest["id"],
                    manifest["href"],
                    manifest["media-type"],
                    ]
                print('\t'.join(parts))

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ListManifestProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--format',
            default='tsv',
            choices=['tsv'],
            type=str,
            help="Lists the output format: tsv.")
