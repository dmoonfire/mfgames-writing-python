"""The various processes for querying and manipulating the spine inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class SpineListProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and lists the spine entries."""

    def get_help(self):
        return "Lists the spines of a OPF."

    def report_tsv(self):
        for spine_id in sorted(self.opf.spine_itemrefs):
            fields = self.get_manifest(spine_id)
            print('\t'.join(fields))


class SpineRemoveProcess(writing.opf.ManipulateOpfFileProcess):
    def get_help(self):
        return "Removes an entry in the spine."

    def manipulate(self):
        pass

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(SpineRemoveProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The ID for the spine entry")


class SpineSetProcess(writing.opf.ManipulateOpfFileProcess):
    """Sets an item in the spine"""

    def get_help(self):
        return "Replaces or adds an entr in the spine."

    def manipulate(self):
        self.opf.spine_itemrefs.append(self.args.id)

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(SpineSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The ID for the spine entry")
