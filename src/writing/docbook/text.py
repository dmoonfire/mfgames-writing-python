import abc
import codecs
import logging
import os
import re
import textwrap
import xml.sax

import writing.constants
import writing.process


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

        chunk_chapter = scanner.process.args.chunk_chapter

        if xml_element == "chapter" and chunk_chapter != 'no':
            filename = chunk_chapter.format(
                id=self.docbook_id,
                number=self.parent.get_element_number(xml_element))
            self.output_filename = scanner.get_output_filename(filename)
            self.output_depth = 0

    def get_element_number(self, docbook_element):
        """Determines the index of a given 1-based index in the parent
        and returns it.

        If this is given a non-existant parent, then it will just return 0.
        """

        # If we don't exist, then just return 0.
        if not self:
            return 0;
        
        # Otherwise, start at 1 and total up every element that has
        # the same docbook element name as given.
        count = 1

        for entry in self.children:
            if entry.docbook_element == docbook_element:
                count = count + 1

        return count

    def dump_self(self):
        if self.output_filename:
            output_filename = ', output=' + self.output_filename
        else:
            output_filename = ''

        if self.docbook_id:
            docbook_id = ', id=' + self.docbook_id
        else:
            docbook_id = ''

        if self.title:
            title = self.title
        else:
            title = '<No Title>'

        prefix = '    ' * self.output_depth

        print('%d %s%s [%s%s%s]' % (
            self.input_depth,
            prefix,
            title,
            self.docbook_element,
            docbook_id,
            output_filename))

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
        if not schema:
            schema = None

        if schema not in self.subjectsets:
            self.subjectsets[schema] = []

        self.subjectsets[schema].append(term)

    def dump_entry(self):
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

    def characters(self, contents):
        if self.capture_buffer:
            self.buffer += contents

    def startElement(self, name, attrs):
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

class ConvertToTextFilesProcess(
    writing.process.ConvertFilesProcess,
    xml.sax.ContentHandler):
    """Basic conversion process for Docbook into various text formats."""
    
    _log = logging.getLogger('text')

    def __init__(self):
        self.structure_index = 0
        self.buffer = unicode()
        self.output = None

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """

        self.args = args

        # If we have chunking, then we need to only have one input file.
        if args.chunk_chapter != 'no' and len(args.files) != 1:
            self.log.exception('The --chunk option can only be used with '
                + 'a single file.')
            return

        # Pass 1: Structure
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

        # Pass 2: Output
        # Go through the file and create the actual output based on
        # the structure parsed above.
        parser = xml.sax.make_parser()
        parser.setContentHandler(self)
        parser.parse(open(input_filename))

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for DocBook text conversion."""

        # Add in the argument from the base class.
        super(ConvertToTextFilesProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--chunk-chapter',
            default='no',
            type=str,
            help="If not set to 'no', will chunk at chapters using the "
                + "value with substituting {id} and {number} in the string.")
        parser.add_argument(
            '--columns',
            default=0,
            type=int,
            help="Sets the number of columns to wrap output.")
        parser.add_argument(
            '--dump-structure',
            default=False,
            const=True,
            nargs='?',
            help="If set, the file structure will be dumped to stdout.") 
        parser.add_argument(
            '--no-newlines',
            dest='newlines',
            const=False,
            default=True,
            nargs='?',
            help="If set, no newlines will be generated between paragraphs.")
        parser.add_argument(
            '--quotes',
            default='simple',
            choices=['simple', 'unicode'],
            type=str,
            help="Determines how quotes are rendered.")
        parser.add_argument(
            '--subjectset-position',
            default='none',
            choices=['none', 'section-top', 'document-bottom'],
            type=str,
            help="Determines where subject sets will be rendered.")

    def characters(self, contents):
        self.buffer += contents
        
    def startElement(self, name, attrs):
        # Check for structural elements, if we have one, then
        # replace the current entry we are processing.
        if is_structural(name):
            # Update where we are in the document
            self.structure_entry = self.structure.entries[self.structure_index]
            self.structure_index = self.structure_index + 1

            # Check to see if we need to open a new output file.
            if self.structure_entry.output_filename:
                # Close the old file, if we have one
                self.close_output()

                # Open a new output file and keep the handle.
                self.buffer = unicode()
                self.output = codecs.open(
                    self.structure_entry.output_filename,
                    'w',
                    'utf-8')
                self.structure_output = self.structure_entry

            # Write out the structure header.
            self.write_structure()

        # If we are starting a quote, add it.
        if name == "quote":
            self.append_quote(True)

        # Handle paragraphs and simple paragraphs
        if name == "simpara" or name == "para":
            # But a blank line before the paragraph.
            self.write_newline()

            # Give the opportunity for the parser to write out the
            # subjectset information at the top of the section.
            self.write_subjectsets_position('section-top')

            # Clear the buffer
            self.buffer = unicode()

    def endElement(self, name):
        if name == "quote":
            self.append_quote(False)

        if name == "simpara":
            self.output.write(self.wrap_buffer())
            self.output.write(os.linesep)
            self.buffer = ""

    def endDocument(self):
        # If we have an open file, then close it.
        self.close_output()

    def append_quote(self, opening):
        if self.args.quotes == 'simple':
            self.buffer += '"'
        if self.args.quotes == 'unicode':
            if opening:
                self.buffer += unichr(8220)
            else:
                self.buffer += unichr(8221)

    def close_output(self):
        """Closes the currently open file, writing out subjectsets if needed."""

        # If we don't have anything open, we don't need to do anything.
        if not self.output:
            return

        # Attempt to write out the subjectsets if we have them.
        self.write_subjectsets_position('document-bottom')

        # Close the handle to the file.
        self.output.close()

    def wrap_buffer(self):
        # Pull out the buffer and clean up the results, removing extra
        # whitespace and filling to the given columns.
        results = self.buffer
        results = results.strip()
        results = re.sub(r'\s+', ' ', results)
        results = re.sub(r'\s+', ' ', results, re.MULTILINE)

        if self.args.columns > 0:
            results = self.wrapper.fill(results)

        return results

    def write_newline(self):
        """Writes out a newline if there should be one."""
        
        if self.args.newlines:
            self.output.write(os.linesep)

    def write_structure(self):
        """Writes out the structure elements."""

        # If we are not the top-most element, we need an extra newline
        # before the header.
        if self.structure_entry.output_depth > 0:
            self.write_newline()

        # Write out the structure header in the file-specific format.
        self.write_structure_header(self.structure_entry)

        # Put in the optional subject sets.
        self.write_subjectsets_position('section-top')

    @abc.abstractmethod
    def write_structure_header(self, structure):
        """Writes out the header for the structure entry."""

    def write_subjectsets(self, subjectsets):
        """Writes out the subjectsets to the output."""

    def write_subjectsets_position(self, position):
        """Writes out the subjectsets if they are in the right position.

        Determines if the subject set should be written out and
        cleared. The position given (e.g., section-top,
        document-bottom) will match the position given in the
        arguments.
        """

        # Check the position given and see if it matches the position
        # given in the arguments. If they don't match, then we won't
        # be writing out the subjectsets.
        if position != self.args.subjectset_position:
            return

        # If we are a document-level position, then we need to gather
        # up all the subjectsets from this level and its
        # children. Otherwise, we just get it from the current
        # structure element.
        if position == 'document-bottom':
            subjectsets = {}
            self.structure_output.get_subjectsets(subjectsets)
        else:
            subjectsets = self.structure_entry.subjectsets

        # If we don't have any subject sets, then don't bother doing
        # anything.
        if len(subjectsets) == 0:
            return

        # We are in the right position and we have at least one parsed
        # subject set, so allow the derived parser to generate it.
        self.write_newline()
        self.write_subjectsets(subjectsets)


class ConvertToCreoleFilesProcess(ConvertToTextFilesProcess):
    """Handles the conversion from DocBook to Creole."""

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Docbook to Creole
        conversion.
        """

        # Add in the argument from the base class.
        super(ConvertToCreoleFilesProcess, self).setup_arguments(parser)

        # Add the Creole-conversion specific processes.
        parser.add_argument(
            '--subjectset-format',
            default='none',
            choices=['none', 'list', 'dokuwiki-tags'],
            type=str,
            help='Determines how subject sets are formatted.')

    def get_extension(self):
        """Defines the BBCode extension as .bbcode"""
        return "creole"

    def get_help(self):
        """Contains the help string for the process."""
        return "Converts DocBook files into Creole."

    def write_structure_header(self, structure):
        """Writes out the header for the structure entry."""

        # If there is no contents of the header, just put in a
        # horizontal line. Otherwise
        if not structure.title:
            self.output.write('----' + os.linesep)
            return

        # Write out the header according to the WikiCreole format.
        self.output.write('{0} {1} {0}'.format(
            '=' * (structure.output_depth + 1),
            structure.title))
        self.output.write(os.linesep)

    def write_subjectsets(self, subjectsets):
        """Writes out the subjectsets to the output."""

        # If we are in the list format, just write it out as a
        # recursive list.
        if self.args.subjectset_format == 'list':
            # Write out the default items first, if we have them.
            if None in subjectsets:
                for subjectterm in subjectsets[None]:
                    self.output.write('* ' + subjectterm)
                    self.output.write(os.linesep)

            # Sort the list of remaining keys, which won't include the
            # None default key.
            keys = subjectsets.keys()
            keys.sort()

            for subjectset in subjectsets.keys():
                if subjectset:
                    # Write out the schema for the subject.
                    self.output.write('* ' + subjectset)
                    self.output.write(os.linesep)

                    # Write out the terms.
                    for subjectterm in subjectsets[subjectset]:
                        self.output.write('** ' + subjectterm)
                        self.output.write(os.linesep)

        # If we are doing Dokuwiki Tags, write them out.
        if self.args.subjectset_format == 'dokuwiki-tags':
            # Create a single list of all the tags at this point.
            tags = []

            for schema in subjectsets.keys():
                for term in subjectsets[schema]:
                    if term not in tags:
                        # If the tag has a _, it will be changed back
                        # to a space character.
                        tags.append(term.replace(' ', '_'))

            tags.sort()

            # Create the dokuwiki tags.
            self.output.write("{{tag>")
            self.output.write(" ".join(sorted(tags)))
            self.output.write("}}")
            self.output.write(os.linesep)


class ConvertToBBCodeFilesProcess(ConvertToTextFilesProcess):
    """Handles the conversion from DocBook to BBCode."""

    def get_extension(self):
        """Defines the BBCode extension as .bbcode"""
        return "bbcode"

    def get_help(self):
        """Contains the help string for the process."""
        return "Converts DocBook files into BBCode."

    def write_structure_header(self, structure):
        """Writes out the header for the structure entry."""

        # If there is no contents of the header, just put in a
        # horizontal line. Otherwise
        if not structure.title:
            self.output.write('----' + os.linesep)
            return

        # Level 0 (top) is bold and italic.
        if structure.output_depth == 0:
            self.output.write('[b][i]{0}[/i][/b]'.format(
                structure.title))
            self.output.write(os.linesep)
            return

        # Level 1 is bold.
        if structure.output_depth == 0:
            self.output.write('[b]{0}[/b]'.format(
                structure.title))
            self.output.write(os.linesep)
            return

        # Level 2 is italic.
        if structure.output_depth == 0:
            self.output.write('[i]{0}[/i]'.format(
                structure.title))
            self.output.write(os.linesep)
            return

        # Beyond this point, we can't handle it in this format.
        raise ProcessException(
            "Cannot handle BBCode depth " + structure.output_depth)
