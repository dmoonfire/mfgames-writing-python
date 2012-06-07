"""The various processes for querying and manipulating the title inside an NCX file."""


import codecs
import os
import sys
import mfgames_writing.ncx
import xml


class TitleGetProcess(mfgames_writing.ncx.ReportNcxFileProcess):
    """Scans the NCX file and gets the title."""

    def get_help(self):
        return "Gets the title entry."

    def report_tsv(self):
        fields = [ self.ncx.title ]
        print('\t'.join(fields))


class TitleSetProcess(mfgames_writing.ncx.ManipulateNcxFileProcess):
    """Sets the title to a manifest entry."""

    def get_help(self):
        return "Sets the title in the file."""

    def manipulate(self):
        self.ncx.title = self.args.title

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(TitleSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'title',
            type=str,
            help="The name of the title")
