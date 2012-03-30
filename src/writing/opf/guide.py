"""The various processes for querying and manipulating the guide inside an OPF file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.opf


class GuideListProcess(writing.opf.ReportOpfFileProcess):
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
