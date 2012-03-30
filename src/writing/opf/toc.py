"""The various processes for querying and manipulating the TOC inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class TocGetProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and gets the TOC entries."""

    def get_help(self):
        return "Gets the TOC entries of a OPF."

    def report_tsv(self):
        fields = self.get_manifest(self.opf.spine_toc)
        print('\t'.join(fields))


class TocSetProcess(writing.opf.ManipulateOpfFileProcess):
    """Sets the toc to a manifest entry."""

    def get_help(self):
        return "Sets the given toc to an item in the manifest."""

    def manipulate(self):
        manifest = self.opf.manifest_items[self.args.id]
        self.opf.spine_toc = self.args.id

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(TocSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The manifest ID of the toc")

