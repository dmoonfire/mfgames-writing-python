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
