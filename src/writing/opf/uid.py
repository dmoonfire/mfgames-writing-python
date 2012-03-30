"""The various processes for querying and manipulating the UID inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class UidGetProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and gets the UID entries."""

    def get_help(self):
        return "Gets the UID entries of a OPF."

    def report_tsv(self):
        fields = [ self.opf.uid ]
        print('\t'.join(fields))


class UidSetProcess(writing.opf.ManipulateOpfFileProcess):
    """Sets the uid to a manifest entry."""

    def get_help(self):
        return "Sets the given uid to an item in the manifest."""

    def manipulate(self):
        self.opf.uid = self.args.uid

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(UidSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'uid',
            type=str,
            help="The new identifier for the OPF")

