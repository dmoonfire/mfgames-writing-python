"""The various processes for querying and manipulating the manifests inside an OPF file."""


import codecs
import mfgames_writing.opf
import os
import sys
import xml


class ManifestListProcess(mfgames_writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and lists the manifest entries."""

    def get_help(self):
        return "Lists the manifests of a OPF."

    def report_tsv(self):
        # Loop through all the manifests in sorted order.
        for manifest_id in sorted(self.opf.manifest_items.keys()):
            fields = self.get_manifest(manifest_id)
            print('\t'.join(fields))


class ManifestRemoveProcess(mfgames_writing.opf.ManipulateOpfFileProcess):
    def get_help(self):
        return "Removes an entry in the manifest."

    def manipulate(self):
        del self.opf.manifest_items[self.args.id]

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ManifestRemoveProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The ID for the manifest entry")


class ManifestSetProcess(mfgames_writing.opf.ManipulateOpfFileProcess):
    """Sets an item in the manifest"""

    def get_help(self):
        return "Replaces or adds an entr in the manifest."

    def manipulate(self):
        record = {
            'id': self.args.id,
            'href': self.args.href,
            'media-type': self.args.type,
            }
        self.opf.manifest_items[self.args.id] = record

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ManifestSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The ID for the manifest entry")
        parser.add_argument(
            'href',
            type=str,
            help="The relative href for the entry.")
        parser.add_argument(
            'type',
            type=str,
            help="The media type (mime) for the entry.")

