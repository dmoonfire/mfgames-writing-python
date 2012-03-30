"""Top-level module for OPF writing utilities."""


import tools.process
import xml.sax


class _OpfScanner(xml.sax.ContentHandler):
    """Scans an OPF file and populates the internal structure."""

    def __init__(self, opf):
        xml.sax.ContentHandler.__init__(self)

        self.buffer = ""
        self.buffer_capture = False
        self.opf = opf

    def characters(self, contents):
        if self.buffer_capture:
            self.buffer += contents

    def startElement(self, name, attrs):
        # Process the manifest elements.
        if name == "item":
            # Save the attributes as the record, keyed by the id.
            self.opf.manifest_items[attrs["id"]] = attrs

        # Process the guide elements.
        if name == "reference":
            # Save the attributes as the record, keyed by the type.
            self.opf.guide_references[attrs["type"]] = attrs

        # Process the spine elements.
        if name == "spine":
            self.opf.spine_toc = attrs["toc"]

        if name == "itemref":
            self.opf.spine_itemrefs.append(attrs["idref"])

        # Process the metadata elements.
        if name == "meta":
            self.opf.metadata_meta[attrs["name"]] = attrs["content"]

        if name.startswith("dc:"):
            # The Dublin Core elements are in the content string.
            self.buffer_capture = True

    def endElement(self, name):
        # Check for the Dublin Core elements
        if name.startswith("dc:"):
            # Save the components of the DC element.
            self.opf.metadata_dc[name[3:]] = self.buffer

            # Stop the capturing process
            self.buffer_capture = False
            self.buffer = ""


class Opf():
    def __init__(self):
        self.guide_references = {}
        self.manifest_items = {}
        self.metadata_meta = {}
        self.metadata_dc = {}
        self.spine_itemrefs = []
        self.spine_toc = None


class InputOpfFileProcess(tools.process.InputFileProcess):
    """Imports the OPF file into memory."""

    def __init__(self):
        super(InputOpfFileProcess, self).__init__()
        self.opf = None

    def get_manifest(self, manifest_id):
        """Returns the three components of a manifest."""
        manifest = self.opf.manifest_items[manifest_id]
        fields = [
            manifest["id"],
            manifest["href"],
            manifest["media-type"]]
        return fields

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(InputOpfFileProcess, self).process(args)

        # Create a SAX parser to go through the file looking for
        # DC entries.
        self.opf = Opf()
        scanner = _OpfScanner(self.opf)
        parser = xml.sax.make_parser()
        parser.setContentHandler(scanner)
        parser.parse(open(args.file))


class ReportOpfFileProcess(InputOpfFileProcess):
    """Base class to report the contents of an OPF file."""

    def __init__(self):
        super(ReportOpfFileProcess, self).__init__()
        self.report_format = None

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(ReportOpfFileProcess, self).process(args)

        # Save the report format.
        self.report_format = args.format

        # Call the individula format methods, if they are overriden.
        if args.format == 'tsv':
            self.report_tsv()

    def report_tsv(self):
        """Writes out the TSV report for the process."""
        pass

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ReportOpfFileProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--format', '-f',
            default='tsv',
            choices=['tsv'],
            type=str,
            help="Gets the output format: tsv.")
