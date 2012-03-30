"""The various processes for querying and manipulating the TOC inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class CoverGetProcess(writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and gets the TOC entries."""

    def get_help(self):
        return "Gets the cover entry."

    def report_tsv(self):
        fields = self.get_manifest(self.opf.metadata_meta["cover"])
        print('\t'.join(fields))
