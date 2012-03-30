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
