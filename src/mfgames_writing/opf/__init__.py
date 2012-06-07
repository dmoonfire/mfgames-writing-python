"""Top-level module for OPF writing utilities."""


from xml.dom.minidom import Document
import abc
import codecs
import datetime
import mfgames_tools.process
import os
import re
import sys
import xml.sax


class _OpfScanner(xml.sax.ContentHandler):
    """Scans an OPF file and populates the internal structure."""

    def __init__(self, opf):
        xml.sax.ContentHandler.__init__(self)

        self.buffer = ""
        self.buffer_capture = False
        self.opf = opf
        self.parsed_id = None

    def characters(self, contents):
        if self.buffer_capture:
            self.buffer += contents

    def startElement(self, name, attrs):
        # Process the package
        if name == "package":
            self.opf.uid_id = attrs["unique-identifier"]

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
            self.buffer_capture = True
            self.parsed_id = attrs["name"]

        if name.startswith("dc:"):
            # The Dublin Core elements are in the content string.
            self.buffer_capture = True

            # If there an id field, we set it so we can use it after
            # we finish the element parsing.
            self.parsed_id = None

            if "id" in attrs:
                self.parsed_id = attrs["id"]

    def endElement(self, name):
        # Check for the Dublin Core elements
        if name.startswith("dc:"):
            # Figure out the name. It always starts with the elements
            # after the dc: tag (e.g., "dc:identifier" would be
            # "identifier). If there is an id field, then we append
            # that to the name with a hash prefix.
            dc_type = name[3:]

            if self.parsed_id:
                dc_type += "#" + self.parsed_id

            # Save the components of the DC element.
            self.opf.metadata_dc[dc_type] = self.buffer

            # Stop the capturing process
            self.buffer_capture = False
            self.buffer = ""

        if name == "meta":
            # Save the value.
            self.opf.metadata_meta[self.last_id] = self.buffer

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
        self.uid_id = None


class InputOpfFileProcess(mfgames_tools.process.InputFileProcess):
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

        # Make sure the data is normalized. dcterms:modified is a
        # required field, so we fake it with the timestamp of the file
        # if we don't have anything else.
        if not "dcterms:modified" in self.opf.metadata_meta:
            file_stats = os.stat(args.file)
            file_time = file_stats.st_mtime
            file_timestamp = datetime.datetime.fromtimestamp(file_time)
            self.opf.metadata_meta["dcterms:modified"] = file_timestamp.isoformat()


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


class ManipulateOpfFileProcess(InputOpfFileProcess):
    """Base class for processes that load in an OPF, make changes, and
    write it out either in place or to an output file."""

    def __init__(self):
        super(ManipulateOpfFileProcess, self).__init__()
        self.report_format = None

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(ManipulateOpfFileProcess, self).process(args)

        # Call the manipulate method to make the changes.
        self.manipulate()

        # If the output file is not defined, write it in place.
        if self.args.output == None:
            self.args.output = self.args.file

        # Get the handle to the output.
        if self.args.output == "-":
            output = sys.stdout
        else:
            output = codecs.open(self.args.output, 'w', 'utf-8')

        # Write the resulting file out to the given stream.
        self.write_output(output)

    @abc.abstractmethod
    def manipulate(self):
        """Manipulates the contents of the OPF file."""
        pass

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ManipulateOpfFileProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--output', '-o',
            default=None,
            type=str,
            help="Writes the results to the given file, or in place if missing.")

    def write_output(self, output):
        """Writes the NCX file to the given handle."""

        # Create the XML document.
        doc = Document()

        # Create the OPF tag.
        opf = doc.createElement("package")
        doc.appendChild(opf)
        opf.setAttribute("unique-identifier", self.opf.uid_id)
        opf.setAttribute("version", "3.0")
        opf.setAttribute("xmlns", "http://www.idpf.org/2007/opf")
        opf.setAttribute("xmlns:dc", "http://purl.org/dc/elements/1.1/")

        # Create the metadata element.
        metadata = doc.createElement("metadata")
        opf.appendChild(metadata)

        for dc in sorted(self.opf.metadata_dc.keys()):
            # Get the dc tag and break out the ID field if we have one.
            matches = re.search("^(.*?)#(.*?)$", dc)
            name = dc
            name_id = None

            if matches:
                name = matches.group(1)
                name_id = matches.group(2)

            # Create the element and optional ID field.
            element = doc.createElement("dc:" + name)

            if name_id:
                element.attributes["id"] = name_id

            # Write out the contents of the DC tag.
            contents = self.opf.metadata_dc[dc]
            element.appendChild(doc.createTextNode(contents))

            # Append the DC element to the metadata parent.
            metadata.appendChild(element)

        for name in sorted(self.opf.metadata_meta.keys()):
            content = self.opf.metadata_meta[name]
            element = doc.createElement("meta")
            element.setAttribute("property", name)
            element.appendChild(doc.createTextNode(content))

            metadata.appendChild(element)

        # Create the manifest elements.
        manifest = doc.createElement("manifest")
        opf.appendChild(manifest)

        for manifest_id in sorted(self.opf.manifest_items.keys()):
            fields = self.get_manifest(manifest_id)
            element = doc.createElement("item")
            element.setAttribute("id", fields[0])
            element.setAttribute("href", fields[1])
            element.setAttribute("media-type", fields[2])

            # Finish adding the child to the list.
            manifest.appendChild(element)

        # Create the spine elements.
        spine = doc.createElement("spine")
        spine.setAttribute("toc", self.opf.spine_toc)
        opf.appendChild(spine)

        for spine_id in sorted(self.opf.spine_itemrefs):
            element = doc.createElement("itemref")
            element.setAttribute("idref", spine_id)

            spine.appendChild(element)

        # Create the guide elements.
        guide = doc.createElement("guide")
        opf.appendChild(guide)

        for guide_id in sorted(self.opf.guide_references.keys()):
            g = self.opf.guide_references[guide_id]

            element = doc.createElement("reference")
            element.setAttribute("type", g["type"])
            element.setAttribute("title", g["title"])
            element.setAttribute("href", g["href"])

            guide.appendChild(element)

        # Print out the resulting file.
        doc.writexml(output, encoding='utf-8', newl="\n", addindent="\t")
