"""The various processes for querying and manipulating the TOC inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class CoverGetProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and gets the TOC entries."""

    def get_help(self):
        return "Gets the cover entry."

    def report_tsv(self):
        fields = self.get_manifest(self.opf.metadata_meta["cover"])
        print('\t'.join(fields))


class CoverSetProcess(writing.opf.ManipulateOpfFileProcess):
    """Sets the cover to a manifest entry."""

    def get_help(self):
        return "Sets the given cover to an item in the manifest."""

    def manipulate(self):
        manifest = self.opf.manifest_items[self.args.id]
        self.opf.metadata_meta["cover"] = self.args.id

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(CoverSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The manifest ID of the cover")
