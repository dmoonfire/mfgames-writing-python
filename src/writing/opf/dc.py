"""The various processes for querying and manipulating the Dublin Core inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class DublinCoreListProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and lists the Dublin Core entries."""

    def get_help(self):
        return "Lists the Dublin Core entries of a OPF."

    def report_tsv(self):
        for dc in sorted(self.opf.metadata_dc.keys()):
            dc_contents = self.opf.metadata_dc[dc]
            fields = [dc, dc_contents]
            print('\t'.join(fields))


class DublinCoreRemoveProcess(writing.opf.ManipulateOpfFileProcess):
    def get_help(self):
        return "Removes a given Dublin Core fields."

    def manipulate(self):
        del self.opf.metadata_dc[self.args.key]
        pass

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(DublinCoreRemoveProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'key',
            type=str,
            help="The Dublin Core field, without the leading dc: (e.g., Creator)")


class DublinCoreSetProcess(writing.opf.ManipulateOpfFileProcess):
    """Scans the OPF file and lists the Dublin Core entries."""

    def get_help(self):
        return "Sets the given Dublin Core field to the given value."

    def manipulate(self):
        self.opf.metadata_dc[self.args.key] = self.args.value

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(DublinCoreSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'key',
            type=str,
            help="The Dublin Core field, without the leading dc: (e.g., Creator)")
        parser.add_argument(
            'value',
            type=str,
            help="The value for the field.")

