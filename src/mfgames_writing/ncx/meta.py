"""The various processes for querying and manipulating the Meta inside an NCX file."""


import codecs
import mfgames_writing.ncx
import os
import sys
import xml


class MetaListProcess(mfgames_writing.ncx.ReportNcxFileProcess):
    """Scans the NCX file and lists the meta entries."""

    def get_help(self):
        return "Lists the meta entries of a NCX."

    def report_tsv(self):
        for name in sorted(self.ncx.meta.keys()):
            value = self.ncx.meta[name]
            fields = [name, value]
            print('\t'.join(fields))


class MetaRemoveProcess(mfgames_writing.ncx.ManipulateNcxFileProcess):
    def get_help(self):
        return "Removes a given meta fields."

    def manipulate(self):
        del self.ncx.meta[self.args.key]

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(MetaRemoveProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'key',
            type=str,
            help="The Meta field, without the leading dc: (e.g., Creator)")


class MetaSetProcess(mfgames_writing.ncx.ManipulateNcxFileProcess):
    """Scans the NCX file and lists the meta entries."""

    def get_help(self):
        return "Sets the given meta field to the given value."

    def manipulate(self):
        self.ncx.meta[self.args.key] = self.args.value

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(MetaSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'key',
            type=str,
            help="The meta field, including any namespace such as dtd:")
        parser.add_argument(
            'value',
            type=str,
            help="The value for the field.")

