"""Top-level module for OPF writing utilities."""


import xml.sax


class _OpfScanner(xml.sax.ContentHandler):
    """Scans an OPF file and populates the internal structure."""

    def __init__(self, opf):
        xml.sax.ContentHandler.__init__(self)

        self.opf = opf

    # def characters(self, contents):
    #     """Processes character from the XML stream."""

    #     if self.capture_buffer:
    #         self.buffer += contents

    def startElement(self, name, attrs):
        if (name == "item"):
            # Save the attributes as the record.
            self.opf.manifest_items[attrs["id"]] = attrs

    def endElement(self, name):
        pass #print("-" + name)


class Opf():
    def __init__(self):
        self.manifest_items = {}
