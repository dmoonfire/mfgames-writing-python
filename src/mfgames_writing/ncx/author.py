"""The various processes for querying and manipulating the author inside an NCX file."""


import codecs
import mfgames_writing.ncx
import os
import sys
import xml


class AuthorGetProcess(mfgames_writing.ncx.ReportNcxFileProcess):
    """Scans the NCX file and gets the author."""

    def get_help(self):
        return "Gets the author entry."

    def report_tsv(self):
        fields = [ self.ncx.author ]
        print('\t'.join(fields))


class AuthorSetProcess(mfgames_writing.ncx.ManipulateNcxFileProcess):
    """Sets the author to a manifest entry."""

    def get_help(self):
        return "Sets the author in the file."""

    def manipulate(self):
        self.ncx.author = self.args.author

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(AuthorSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'author',
            type=str,
            help="The name of the author")
