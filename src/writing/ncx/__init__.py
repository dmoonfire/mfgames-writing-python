"""Top-level module for NCX writing utilities."""


import abc
import tools.process
import xml.sax


class _NcxScanner(xml.sax.ContentHandler):
    """Scans an NCX file and populates the internal structure."""

    def __init__(self, ncx):
        xml.sax.ContentHandler.__init__(self)

        self.buffer = ""
        self.buffer_capture = False
        self.ncx = ncx
        self.last_nav = None

    def characters(self, contents):
        if self.buffer_capture:
            self.buffer += contents

    def startElement(self, name, attrs):
        # Process the metadata elements.
        if name == "meta":
            # Save the attributes as the record, keyed by the id.
            self.ncx.meta[attrs["name"]] = attrs["content"]

        # Process the navigation elements.
        if name == "navPoint":
            record = [
                attrs["id"],
                "", # text
                "", # href
                ]
            self.ncx.navpoints.append(record)
            self.last_nav = record

        if (name == "text" or
            name == "docTitle" or
            name == "docAuthor"):
            self.buffer_capture = True

        if name == "content":
            self.last_nav[2] = attrs["src"]

    def endElement(self, name):
        clear_buffer = False

        if name == "text":
            self.last_nav[1] = self.buffer
            clear_buffer = True

        if name == "docTitle":
            self.ncx.title = self.buffer
            clear_buffer = True

        if name == "docAuthor":
            self.ncx.author = self.buffer
            clear_buffer = True

        if clear_buffer:
            self.buffer_capture = False
            self.buffer = ""


class Ncx():
    def __init__(self):
        self.meta = {}
        self.navpoints = []
        self.title = None
        self.author = None


class InputNcxFileProcess(tools.process.InputFileProcess):
    """Imports the NCX file into memory."""

    def __init__(self):
        super(InputNcxFileProcess, self).__init__()
        self.ncx = None

    def get_manifest(self, manifest_id):
        """Returns the three components of a manifest."""
        manifest = self.ncx.manifest_items[manifest_id]
        fields = [
            manifest["id"],
            manifest["href"],
            manifest["media-type"]]
        return fields

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(InputNcxFileProcess, self).process(args)

        # Create a SAX parser to go through the file looking for
        # DC entries.
        self.ncx = Ncx()
        scanner = _NcxScanner(self.ncx)
        parser = xml.sax.make_parser()
        parser.setContentHandler(scanner)
        parser.parse(open(args.file))


class ReportNcxFileProcess(InputNcxFileProcess):
    """Base class to report the contents of an NCX file."""

    def __init__(self):
        super(ReportNcxFileProcess, self).__init__()
        self.report_format = None

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(ReportNcxFileProcess, self).process(args)

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
        super(ReportNcxFileProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--format', '-f',
            default='tsv',
            choices=['tsv'],
            type=str,
            help="Gets the output format: tsv.")


class ManipulateNcxFileProcess(InputNcxFileProcess):
    """Base class for processes that load in an NCX, make changes, and
    write it out either in place or to an output file."""

    def __init__(self):
        super(ManipulateNcxFileProcess, self).__init__()
        self.report_format = None

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(ManipulateNcxFileProcess, self).process(args)

        # Call the manipulate method to make the changes.
        self.manipulate()

        # If the output file is not defined, write it in place.
        if self.args.output == None:
            self.args.output = self.args.file

        # Write the resulting file out to the given stream.
        print("Writing out some files!")

    @abc.abstractmethod
    def manipulate(self):
        """Manipulates the contents of the NCX file."""
        pass

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ManipulateNcxFileProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--output', '-o',
            default=None,
            type=str,
            help="Writes the results to the given file, or in place if missing.")

