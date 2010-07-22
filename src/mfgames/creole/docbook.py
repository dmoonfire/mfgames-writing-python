#
# Imports
#

# System Imports
import argparse
import codecs
import logging
import re

# External Imports
from creoleparser.dialects import *
from creoleparser.core import *
from smartypants import smartyPants

# Internal Imports
import mfgames.convert
import mfgames.process

#
# Creole Parser
#

BaseParser = creole11_base()

class DocbookCreoleParser(BaseParser):
    p = Paragraph('para')

#
# Conversion Class
#

class CreoleDocbookConvertProcess(mfgames.convert.ConvertProcess):
    help = 'Converts Creole files into DocBook 5.'

    def get_extension(self):
        return "xml"

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into DocBook.
        """
    
        # Read the file contents into memory. We need to use UTF-8 because
        # the file might have it and we make that assumption.
        input_file = codecs.open(input_filename, mode='r', encoding='utf-8')
        contents = input_file.read()
    
        # Create a parser that convert Creole into something that is
        # roughly DocBook. We'll have to do some additional parsing once
        # we get the file to handle attribute folding, quotes, and
        # sections.
        parser = Parser(
	    dialect=DocbookCreoleParser,
	    method='xml')
    
        # Change the typographical quotes into something aesthetic. We do
        # this before converting from Creole because of the tags created
        # by that parser potentially have quotes themselves.
        contents = smartyPants(contents)
    
        # Convert the file into an XML string. 
        contents = parser(contents)

        # Convert the typographical quotes into <quote> tags.
        contents = re.sub(r'&amp;#(\d+);', r'&#\1;', contents)
        contents = re.sub(r'&#8220;', '<quote>', contents)
        contents = re.sub(r'&#8221;', '</quote>', contents)

        # If we are parsing languages, then convert the language tags
        # (2-3 character tags after a quote) into xml:lang elements.
        if args.languages:
            contents = re.sub(
                r'<quote>(\w{2,3})\s*:\s*',
                r'<quote xml:lang="\1">',
                contents)

        # Normalize the whitespace and trim the leading spaces.
        contents = string.replace(contents, '\n', ' ')
        contents = string.replace(contents, '\r', ' ')
        contents = string.replace(contents, '\t', ' ')
        contents = re.sub(r'\s+', ' ', contents, re.MULTILINE)
        contents = string.replace(contents, '> <', '><')
        
        # Wrap the headings into DocBook sections. We need to first
        # convert the empty elements ("<h2/>") into pairs ("<h2></h2>")
        # because of how this parser works. Then, we go through every
        # heading level from the bottom and wrap it into a section.
        contents = re.sub(r'<h(\d+)/>', r'<h\1></h\1>', contents)
    
        contents = self.wrap_sections(contents, "section", 'h5',
	    [ 'h4', 'h3', 'h2', 'h1' ])
        contents = self.wrap_sections(contents, "section", 'h4',
            [ 'h3', 'h2', 'h1' ])
        contents = self.wrap_sections(contents, "section", 'h3',
            [ 'h2', 'h1' ])
        contents = self.wrap_sections(contents, "section", 'h2',
            [ 'h1' ])
        contents = self.wrap_sections(contents, "article", 'h1',
            [ ])
    
        # Add the namespaces and version to the top-level elements.
        # Add the XML and article headers.
        namespaces = " ".join([
	    "xmlns='http://docbook.org/ns/docbook'",
	    "xmlns:mw='http://mfgames.com/mfgames-writing'" ])
        contents = re.sub(
	    '<article>',
	    '<article ' + namespaces + ' version="5.0">',
	    contents)
        contents = '<?xml version="1.0" encoding="UTF-8"?>' + contents
    
        # Write the contents to the output file.
        output = open(output_filename, 'w')
        output.write(contents)
        output.close()
    
    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Creole to DocBook
        conversion.
        """

        super(CreoleDocbookConvertProcess, self).setup_arguments(parser)

        # Add the Creole-specific options.
        parser.add_argument(
            '--languages',
            action='store_true',
            help='Converts language tags into xml:lang attributes.')

    #
    # Sections
    #
    
    def wrap_sections(self, contents, element, heading, outer_headings):
        """
        Looks for the headings within the contents and coverts them into
        sections that wrap all the lower headings.
        """
    
        # If we don't have a heading of the given type, we don't have to
        # do anything for wrapping.
        heading_regex = "</?" + heading + ">"
    
        if not re.search(heading_regex, contents):
	    return contents
    
        # Split on the headings. The resulting list will have the initial
        # text in the first element, then pairs of elements for every
        # heading past it.
        sections = re.split(heading_regex, contents)
        results = [sections[0]]
    
        # Loop through the resulting section pairs and create the elements.
        for index in range(1, len(sections)):
	    # Don't bother with odd sections since we'll be looping over
	    # them as part of our processing.
	    if index % 2 == 0:
	        continue
    
	    # Pull out the fields.
	    title = sections[index]
	    region = sections[index + 1]
    
	    # If we are at the top-most section (h1), then break out on
	    # the second or later one.
	    if heading == 'h1' and index > 2:
	        log = logging.getLogger('docbook')
	        log.warning('Skipping top section: ' + title)
	        continue
    
	    # Start by appending the section.
	    results.append('<' + element + '>')
    
            if len(title) > 0:
                # Add the title block to the section.
                results.append('<info><title>')
                results.append(title)
                results.append('</title></info>')
    
            # Normally, the section ends at the end of the second element
            # (which contains the body of the section), but if we find a
            # higher-level heading, we close the section off right before
            # it. This is also why we start at the lowest level heading
            # and move through the higher ones.
            if len(outer_headings) > 0:
                # Build a regex for the outer headings.
                outer_regex = r"(<(" + "|".join(outer_headings) + r")>)"
    
                # If we have the regex in the contents, then we need to
                # terminate it there.
                if re.search(outer_regex, region, re.MULTILINE) != None:
                    # We have a outer level heading, so set it and
                    # continue on.
                    results.append(re.sub(
                        outer_regex,
                        '</' + element + r'>\1',
                        region))
                    continue
                # end if
            # end if
    
            # If we got this far, the ending element goes at the end of
            # the contents since there are no outer headings in the
            # contents.
            results.append(sections[index + 1])
            results.append('</' + element + '>')
        # end for
    
        # Return the resulting sections.
        return "".join(results)
