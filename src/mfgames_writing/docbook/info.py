"""The various informational processes for reading a DocBook file and
producing output based on its contents."""


import lxml.etree
import codecs
import mfgames_tools
import mfgames_writing.docbook.scan
import os
import sys
import xml


# The namespaces used as part of the XPath queries.
docbook_ns = "http://docbook.org/ns/docbook"
docbook_lxml_ns = "{%s}" % docbook_ns
xml_ns = {'d': docbook_ns }


def _get_element_value(node, tag, default):
    """Tries to get the first text element of the given tag, or the
    default value if one cannot be found."""

    for child in node.getiterator(docbook_lxml_ns + tag):
        return child.text

    return default


def _get_element_node(node, tag, default):
    """Tries to get the first text element of the given tag, or the
    default value if one cannot be found."""

    for child in node.getiterator(docbook_lxml_ns + tag):
        return child

    return default


class ExtractSubjectsetsProcess(mfgames_tools.process.InputFilesProcess):
    """Scans the DocBook file and extracts the subject sets."""

    def __init__(self):
        super(ExtractSubjectsetsProcess, self).__init__()

        self.args = None
        self.structure = None

    def get_help(self):
        """Returns the help string for the process."""
        return "Extracts subjectsets and terms from the input."

    def process(self, args):
        """Extracts the summaries from the given input files."""

        super(ExtractSubjectsetsProcess, self).process(args)

        self.args = args

        # Figure out the output, if we have one. If we are opening a file
        # then write out the BOM for Unicode.
        if args.output:
            output = codecs.open(
                args.output,
                mode='w',
                encoding='utf-8')
            output.write(codecs.BOM_UTF8)
        else:
            output = sys.stdout

        # Go through all the input files.
        for filename in args.files:
            self.process_file(args, filename, output)

    def process_file(self, args, input_filename, output):
        """Converts the given file into Creole."""

        # Go through the file and build up the structural elements of
        # the document. This is used to determine chunking and file
        # generation.
        self.structure = mfgames_writing.docbook.scan._StructureScanner(
            self,
            '')
        parser = xml.sax.make_parser()
        parser.setFeature(
            "http://xml.org/sax/features/external-general-entities",
            False)
        parser.setContentHandler(self.structure)
        parser.parse(open(input_filename))

        # Get all the subjects from the root element.
        subjectsets = {}
        self.structure.root_entry.get_subjectsets(subjectsets)

        # Check on the output format.
        if args.output_format == 'tsv':
            for subjectset in sorted(subjectsets.keys()):
                # We can have a None for the subject set, replace this with
                # blank.
                setname = subjectset

                if not subjectset:
                    setname = ''

                for subjectterm in sorted(subjectsets[subjectset]):
                    parts = [
                        input_filename,
                        setname,
                        subjectterm]
                    output.write('\t'.join(parts))
                    output.write(os.linesep)

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(ExtractSubjectsetsProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--output',
            type=str,
            help="Output file otherwise use stdout.")
        parser.add_argument(
            '--output-format',
            default='tsv',
            choices=['tsv'],
            type=str,
            help="Lists the output format: tsv.")
        parser.add_argument(
            '--chunk-chapter',
            default='no',
            type=str,
            help="If not set to 'no', will chunk at chapters using the "
                + "value with substituting {id} and {number} in the string.")


class QueryProcess(mfgames_tools.process.InputFilesProcess):
    """
    Scans and filters one or more DocBook files and outputs data from
    those results.
    """

    def __init__(self):
        super(QueryProcess, self).__init__()

    def get_help(self):
        return "Scans DocBook and outputs the results."

    def process(self, args):
        # Call the parent class' implementation which ensures all the
        # files exists and sets up the internal arguments.
        super(QueryProcess, self).process(args)

    def process_file(self, input_filename):
        """Processes a single DocBook 5 file and determines if it
        should be filtered out, if not, then it outputs the
        results."""

        # Load the entire XML file into memory.
        xml = lxml.etree.parse(input_filename)

        # Make some virtual nodes into the XML.
        self.add_virtual_elements(xml, input_filename)

        # TODO: Perform the where clause to filter it out.

        # If we got this far, this file needs to have its fields
        # written out.
        self.select_file(xml)

    def add_virtual_elements(self, xml, filename):
        """Adds in virtual elements into the XML tree to represent
        information about the file or formatting."""

        # Go through all the author tags and add a formatted version.
        for info in xml.xpath("//d:personname", namespaces=xml_ns):
            # Pull out the components of the name.
            firstname = _get_element_value(info, "firstname", None)
            surname = _get_element_value(info, "surname", None)

            name = surname
            
            if firstname:
                name += ", " + firstname

            # Pull the name back in.
            fullname = lxml.etree.Element(docbook_lxml_ns + "fullname")
            fullname.text = name
            info.append(fullname)

        # Go through all the info tags and add a formatted version of
        # the titles.
        for info in xml.xpath("//d:info", namespaces=xml_ns):
            # Pull out the components of the name.
            title = _get_element_value(info, "title", None)
            subtitle = _get_element_value(info, "subtitle", None)

            combined = title
            
            if subtitle:
                combined += ": " + subtitle

            # Pull the name back in.
            fulltitle = lxml.etree.Element(docbook_lxml_ns + "fulltitle")
            fulltitle.text = combined
            info.append(fulltitle)

            # Put in the absolute filename.
            abspath = lxml.etree.Element(docbook_lxml_ns + "abspath")
            abspath.text = os.path.abspath(filename)
            info.append(abspath)

    def select_file(self, xml):
        """Retrieves the fields from the given XML file and writes it
        out to the stream."""

        # Go through the select expressions and process each one.
        fields = []

        # Get the root for the select query and keep it since we'll
        # loop through these quite a few times (once per field).
        select_roots = xml.xpath(self.args.select_root, namespaces=xml_ns)

        # Go through each of the select queries first. We treat these
        # as a single field which we'll combine together.
        for select_xpath in self.args.select:
            # Create a list of results we find from this field, which
            # we'll combine together into a single "field".
            values = []

            # Loop through all the resulting root nodes so we can do a
            # xpath against the root.
            for select_root in select_roots:
                # Perform the query on the select root for the path.
                selects = select_root.xpath(select_xpath, namespaces=xml_ns)

                for select in selects:
                    if isinstance(select, basestring):
                        values.append(select)
                    else:
                        values.append(select.text)

            # Once we finish gathering up all the values, we combine
            # them together and add it to the resulting output fields.
            value_string = ", ".join(values)
            fields.append(value_string)

        # Output the resulting fields to the output stream.
        print "\t".join(fields)

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(QueryProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--select-root',
            default="/*/d:info",
            type=str,
            help="The XPath to the root element for the base of "
            + "all the select queries.")
        parser.add_argument(
            '--select', '-s',
            default=['d:title'],
            type=str,
            nargs='+',
            help="The relative XPath elements to return in the results.")
