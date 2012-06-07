"""The various processes for querying and manipulating the guide inside an OPF file."""


import codecs
import mfgames_writing.opf
import os
import sys
import xml


class GuideListProcess(mfgames_writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and lists the guide entries."""

    def get_help(self):
        return "Lists the guides of a OPF."

    def report_tsv(self):
        # Go through all the (sorted) guides and write themout.
        for guide_id in sorted(self.opf.guide_references.keys()):
            guide = self.opf.guide_references[guide_id]
            parts = [
                guide["type"],
                guide["title"],
                guide["href"],
                ]
            print('\t'.join(self.parts))


class GuideRemoveProcess(mfgames_writing.opf.ManipulateOpfFileProcess):
    def get_help(self):
        return "Removes an entry in the guide."

    def manipulate(self):
        del self.opf.guide_references[self.args.type]

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(GuideRemoveProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'type',
            type=str,
            help="The type for the guide entry")


class GuideSetProcess(mfgames_writing.opf.ManipulateOpfFileProcess):
    """Sets an item in the guide"""

    def get_help(self):
        return "Replaces or adds an entr in the guide."

    def manipulate(self):
        record = [
            self.args.type,
            self.args.title,
            self.args.href,
            ]
        self.opf.guide_references[self.args.type] = record

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(GuideSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'type',
            type=str,
            help="The type for the guide entry")
        parser.add_argument(
            'title',
            type=str,
            help="The title for the entry.")
        parser.add_argument(
            'href',
            type=str,
            help="The relative href for the entry.")
