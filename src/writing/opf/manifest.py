"""The various processes for querying and manipulating the manifests inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class ManifestListProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and lists the manifest entries."""

    def get_help(self):
        return "Lists the manifests of a OPF."

    def report_tsv(self):
        # Loop through all the manifests in sorted order.
        for manifest_id in sorted(self.opf.manifest_items.keys()):
            fields = self.get_manifest(manifest_id)
            print('\t'.join(fields))
