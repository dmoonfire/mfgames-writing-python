"""Handles processing of DocBook files for additional information."""


import codecs
import mfgames_tools.process
import os
import sys
import xml.sax


def is_structural(name):
    """Determines if a specific DocBook element is considered structural.
    
    Structrual elements are ones that would impact headers or
    files of a generated file.
    """

    structure_elements = ["book", "article", "chapter", "section"]    
    return name in structure_elements

class _StructureEntry(object):
    """Defines a structural entry in the input file."""

    def __init__(self, scanner, xml_element, xml_attrs, parent_entry):
        # Set up the initial values for the structure.
        self.scanner = scanner
        self.title = unicode()
        self.children = []
        self.subjectsets = {}
        self.docbook_element = xml_element

        # Determine our depth in the file.
        self.parent = parent_entry

        if parent_entry:
            # Set our depth equal to our parents but one level deeper
            self.input_depth = parent_entry.input_depth + 1
            self.output_depth = parent_entry.output_depth + 1

            # Add ourselves to our parent list
            parent_entry.children.append(self)
        else:
            self.input_depth = 0
            self.output_depth = 0

        # If the DocBook element has an ID, save it
        if xml_attrs.has_key("id"):
            self.docbook_id = xml_attrs["id"]
        else:
            self.docbook_id = None

        # Determine the output filename for this section, if any.
        self.output_filename = None
        self.output_tag = None

        if self.parent:
            self.number = self.parent.get_element_number(xml_element)
        else:
            self.number = 0

        chunk_chapter = scanner.process.args.chunk_chapter

        if xml_element == "chapter" and chunk_chapter != 'no':
            filename = chunk_chapter.format(
                id=self.docbook_id,
                number=self.number)
            self.output_tag = filename
            self.output_filename = scanner.get_output_filename(filename)
            self.output_depth = 0

    def get_element_number(self, docbook_element):
        """Determines the index of a given 1-based index in the parent
        and returns it.

        If this is given a non-existant parent, then it will just return 0.
        """

        # If we don't exist, then just return 0.
        if not self:
            return 0
        
        # Otherwise, start at 1 and total up every element that has
        # the same docbook element name as given.
        count = 0

        for entry in self.children:
            if entry.docbook_element == docbook_element:
                count = count + 1

        return count

    def dump_self(self):
        """Dumps information about the structure itself to stdout."""

        attrs = []

        if self.number > 0:
            attrs.append(' ' + format(self.number))

        if self.output_tag:
            attrs.append(", tag=" + self.output_tag)

        if self.output_filename:
            attrs.append(', output=' + self.output_filename)

        if self.docbook_id:
            attrs.append(', id=' + self.docbook_id)

        if self.title:
            title = self.title
        else:
            title = '<No Title>'

        prefix = '    ' * self.output_depth

        print('%d %s%s [%s%s]' % (
            self.input_depth,
            prefix,
            title,
            self.docbook_element,
            ''.join(attrs)))

    def get_subjectsets(self, subjectsets):
        """Combines all the subjectsets from this entry and its children."""

        # Add our subjectesets to the parameter array.
        for subjectset in self.subjectsets:
            # Add the key if we don't already have it
            if subjectset not in subjectsets:
                subjectsets[subjectset] = []

            # Add all the terms into the resulting object.
            for subjectterm in self.subjectsets[subjectset]:
                if subjectterm not in subjectsets[subjectset]:
                    subjectsets[subjectset].append(subjectterm)

        # Loop through the children and add them to the list
        for child in self.children:
            child.get_subjectsets(subjectsets)

    def add_subjectterm(self, schema, term):
        """Adds a subject term and schema to the entry."""

        if not schema:
            schema = None

        if schema not in self.subjectsets:
            self.subjectsets[schema] = []

        self.subjectsets[schema].append(term)

    def dump_entry(self):
        """Recursively dumps data about the structure to stdout."""

        self.dump_self()

        prefix = '    ' * self.output_depth

        for subjectset in self.subjectsets:
            for subjectterm in self.subjectsets[subjectset]:
                if subjectset:
                    print(prefix + '  * ' + subjectset + ' = ' + subjectterm)
                else:
                    print(prefix + '  * ' + subjectterm)

        for child in self.children:
            child.dump_entry()

class _StructureScanner(xml.sax.ContentHandler):
    """Parses the DocBook XML and identifies the structure."""

    def __init__(self, process, output_filename):
        xml.sax.ContentHandler.__init__(self)

        self.process = process
        self.output_filename = output_filename
        self.entries = []
        self.entry = None
        self.root_entry = None
        self.depth = 0
        self.capture_buffer = False
        self.buffer = unicode()
        self.subjectset_schema = None

    def characters(self, contents):
        """Processes character from the XML stream."""

        if self.capture_buffer:
            self.buffer += contents

    def startElement(self, name, attrs):
        """Processes the beginning of the XML element."""

        if name == "title":
            self.capture_buffer = True

        if is_structural(name):
            # Create a new recursive structure entry.
            self.depth = self.depth + 1
            self.entry = _StructureEntry(
                self,
                name,
                attrs,
                self.entry)

            # If we are the root entry, then we set the filename and
            # add it to the root list.
            if not self.root_entry:
                self.root_entry = self.entry
                self.root_entry.output_filename = self.output_filename
            
            # Add ourselves to the entries so we can look it up again.
            self.entries.append(self.entry)

        # Subject Sets
        if name == "subjectset":
            if 'schema' in attrs:
                self.subjectset_schema = attrs['schema']
            else:
                self.subjectset_schema = None

        if name == "subjectterm":
            self.capture_buffer = True

    def endElement(self, name):
        """Processes the end of the XML element."""

        if name == "title":
            self.entry.title = self.buffer
            self.buffer = unicode()
            self.capture_buffer = False

        if name == "subjectterm":
            self.entry.add_subjectterm(
                self.subjectset_schema, 
                self.buffer.strip())
            self.buffer = unicode()
            self.capture_buffer = False

        if is_structural(name):
            # We need to move up a level and pop off the current
            # entry.
            self.depth = self.depth - 1
            self.entry = self.entry.parent

    def get_output_filename(self, basename):
        """Takes a base filename and adds the same directory and
        extension as the base file."""

        return "{0}{1}{2}.{3}".format(
            os.path.dirname(self.output_filename),
            os.sep,
            basename,
            self.process.get_extension())


class ScanDocbookFilesProcess(mfgames_tools.process.ConvertFilesProcess):
    """Scans the DocBook file and analyzes the structure."""

    def __init__(self):
        super(ScanDocbookFilesProcess, self).__init__()

        self.args = None
        self.structure = None

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """

        self.args = args

        # Go through the file and build up the structural elements of
        # the document. This is used to determine chunking and file
        # generation.
        self.structure = _StructureScanner(self, output_filename)
        parser = xml.sax.make_parser()
        parser.setContentHandler(self.structure)
        parser.parse(open(input_filename))

        if args.dump_structure:
            print('Dumping Structure')
            self.structure.root_entry.dump_entry()
            print('')

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for DocBook scanning."""

        # Add in the argument from the base class.
        super(ScanDocbookFilesProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--chunk-chapter',
            default='no',
            type=str,
            help="If not set to 'no', will chunk at chapters using the "
                + "value with substituting {id} and {number} in the string.")
        parser.add_argument(
            '--dump-structure',
            default=False,
            const=True,
            nargs='?',
            help="If set, the file structure will be dumped to stdout.") 
