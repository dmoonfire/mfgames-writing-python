"""Handles conversion of DocBook to various text and markup formats."""


import abc
import codecs
import logging
import os
import re
import textwrap
import xml.sax

import writing.process
import writing.docbook.scan


class ConvertToTextFilesProcess(
    writing.docbook.scan.ScanDocbookFilesProcess,
    xml.sax.ContentHandler):
    """Basic conversion process for Docbook into various text formats."""
    
    _log = logging.getLogger('text')

    def __init__(self):
        super(ConvertToTextFilesProcess, self).__init__()

        self.structure_index = 0
        self.structure_output = None
        self.structure_entry = None
        self.args = None
        self.buffer = unicode()
        self.output = None
        self.wrapper = None

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """

        self.args = args

        # If we have chunking, then we need to only have one input file.
        if args.chunk_chapter != 'no' and len(args.files) != 1:
            raise writing.process.ProcessError(
                'The --chunk option can only be used with a single file.')

        if args.columns > 0:
            self.wrapper = textwrap.TextWrapper()
            self.wrapper.width = args.columns

        # Call the super implementation.
        super(ConvertToTextFilesProcess, self).convert_file(
            args,
            input_filename,
            output_filename)

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
            '--columns',
            default=0,
            type=int,
            help="Sets the number of columns to wrap output.")
        parser.add_argument(
            '--no-newlines',
            action='store_true',
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
        """Processes a character string in the XML."""
        self.buffer += contents
        
    def startElement(self, name, attrs):
        """Processes the start of the XML element."""

        # Check for structural elements, if we have one, then
        # replace the current entry we are processing.
        if writing.docbook.scan.is_structural(name):
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
        """Processes the end of an XML element."""

        if name == "quote":
            self.append_quote(False)

        if name == "simpara" or name == "para":
            self.output.write(self.wrap_buffer())
            self.output.write(os.linesep)
            self.buffer = ""

    def endDocument(self):
        """Processes the end of an XML document."""

        # If we have an open file, then close it.
        self.close_output()

    def append_quote(self, opening):
        """Appends a normalized quote character to the buffer."""

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

        # If our parent is the book level, write out the table of contents.
        parent = self.structure_entry.parent
        
        if parent:
            if self.structure_entry.number == 1:
                if parent.docbook_element == 'book':
                    self.write_newline()
                    self.write_toc(parent)

        # Attempt to write out the subjectsets if we have them.
        self.write_subjectsets_position('document-bottom')

        # Close the handle to the file.
        self.output.close()

    def wrap_buffer(self):
        """Optionally wraps the output to a given column."""

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
        
        if self.args.no_newlines:
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

    def write_toc(self, structure_entry):
        """Writes out the table of contents."""
        pass

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
        self.output.write(u'{0} {1} {0}'.format(
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

            # Create the dokuwiki tags.
            self.output.write("{{tag>")
            self.output.write(" ".join(sorted(tags)))
            self.output.write("}}")
            self.output.write(os.linesep)

    def write_toc(self, structure_entry):
        """Writes out the table of contents."""

        # Go through and build a tree of all the structure elements.
        for child in structure_entry.children:
            # Only write out the title elements if the child has a title.
            if child.title:
                # Create a nested tree.
                self.output.write('*' * child.input_depth + ' ')

                # If the child has a tag, create a link.
                if child.output_tag:
                    self.output.write('[[')
                    self.output.write(child.output_tag)
                    self.output.write('|')

                self.output.write(child.title)

                # Finish the tag, if we have one
                if child.output_tag:
                    self.output.write(']]')

                # Finish off the line.
                self.output.write(os.linesep)

                # Go through the children's children
                self.write_toc(child)


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
        raise writing.process.ProcessError(
            "Cannot handle BBCode depth " + structure.output_depth)
