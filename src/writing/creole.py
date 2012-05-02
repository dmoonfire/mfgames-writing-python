"""Handles processes for manipulating Creole files."""

import codecs
import logging
import os
import re
import sys

import creoleparser.dialects
import creoleparser.core

sys.path.append('/usr/share/mfgames-writing')
sys.path.append('/usr/local/share/mfgames-writing')

import smartypants
import tools.process
import writing


BaseParser = creoleparser.dialects.creole11_base()


class DocbookCreoleParser(BaseParser):
    """Extends the Creole parser to generate mostly DocBook data."""

    p = creoleparser.dialects.Paragraph('simpara')
    indented = creoleparser.dialects.IndentedBlock(
        'blockquote',
        '>',
        None,
        None)

    simple_element = creoleparser.dialects.SimpleElement(token_dict={
        '**' : 'strong',
        '//' : 'emphasis'})

    li = creoleparser.dialects.ListItem('listitem', list_tokens='*#')
    ol = creoleparser.dialects.List('orderedlist', '#', stop_tokens='*')
    ul = creoleparser.dialects.List('itemizedlist', '*', stop_tokens='#')
    nested_ol = creoleparser.dialects.NestedList('orderedlist', '#')
    nested_ul = creoleparser.dialects.NestedList('itemizedlist', '*')


class CreoleDocbookConvertProcess(tools.process.ConvertFilesProcess):
    """Process for converting Creole files to DocBook."""

    def get_help(self):
        """Returns the help line for the process."""
        return 'Converts Creole files into Docbook 5.'

    def get_extension(self):
        """Returns the extension for files generated by this process."""
        return "xml"

    def convert_file(self, args, input_filename, output_filename):
        """Converts the given file into Docbook."""
    
        # Get the logging context.
        log = logging.getLogger('docbook')

        # Read the file contents into memory. We need to use UTF-8 because
        # the file might have it and we make that assumption.
        input_file = codecs.open(input_filename, mode='r', encoding='utf-8')
        contents = input_file.read()

        # If we are removing commented lines, do it before we convert
        # from Creole. Commented lines start with "#", which is
        # normally a Creole numbered list (which probably won't show
        # up in normal prose).
        if args.enable_comments:
            new_contents = []

            for line in contents.split("\n"):
                if not line.startswith("#"):
                    new_contents.append(line)

            contents = "\n".join(new_contents)
    
        # Create a parser that convert Creole into something that is
        # roughly Docbook. We'll have to do some additional parsing once
        # we get the file to handle attribute folding, quotes, and
        # sections.
        parser = creoleparser.core.Parser(
            dialect=DocbookCreoleParser,
            method='xml')

        # Normalize the construct of '"something-"' into something
        # SmartyPants can handle.
        contents = contents.replace('-"', '--"')
        contents = contents.replace('"-', '"--')
    
        # Change the typographical quotes into something aesthetic. We
        # do this before converting from Creole because of the tags
        # created by that parser potentially have quotes
        # themselves. We split this into different elements to speed
        # up the regex as part of the conversion.
        log.debug('Formatting normal quotes into typographic ones')
        parts = unicode.split(contents, '\n\n')

        for index in range(len(parts)):
            parts[index] = smartypants.smartyPants(parts[index])

        contents = '\n\n'.join(parts)
    
        # Convert the file into an XML string.
        log.debug('Converting Creole to XML')
        contents = parser(contents)

        # Start by initializing the namespaces.
        namespaces = [writing.DOCBOOK_NAMESPACE]

        # If we need to number the paragraphs, we do that and add the
        # namespace for the numbering elements.
        if args.number_paragraphs:
            # Add the namespace so we can add an attribute.
            namespaces.append(writing.MFGAMES_NAMESPACE)

            # Go through all the paragraphs and number them
            contents = self.number_paragraphs(contents)

        # Convert the typographical quotes into formatted quotes. If
        # the user has requested they be converted into Docbook
        # <quote> tags, we do that now.
        log.debug('Changing quotes into DocBook quote tags')
        contents = re.sub(r'&amp;#(\d+);', r'&#\1;', contents)
        
        if args.convert_quotes:
            contents = re.sub(r'&#8220;', '<quote>', contents)
            contents = re.sub(r'&#8221;', '</quote>', contents)

        # Normalize the whitespace and trim the leading spaces.
        log.debug('Normalizing whitespace and paragraphs')
        contents = contents.replace('\n', ' ')
        contents = contents.replace('\r', ' ')
        contents = contents.replace('\t', ' ')
        contents = re.sub(r'\s+', ' ', contents, re.MULTILINE)
        contents = contents.replace('<simpara> ', '<simpara>')
        contents = contents.replace(' </simpara> ', '</simpara>')

        # Fix the strong tags and make them emphasis.
        contents = contents.replace(
            '<strong>',
            '<emphasis role="strong">')
        contents = contents.replace(
            '</strong>',
            '</emphasis>')
        
        # Convert the image tags into the DocBook versions.
        contents = re.sub(
            r'<img src="(.*?)".*?/>',
            r'<mediaobject><imageobject>'
            + r'<imagedata align="center" fileref="\1"/>'
            + r'</imageobject></mediaobject>',
            contents)

        # Convert backticks into foreignphrases.
        if args.parse_backticks:
            contents = re.sub(
                r'`(.*?)`',
                r'<foreignphrase>\1</foreignphrase>',
                contents)

        # If we are parsing languages, then convert the language tags
        # (2-3 character tags after a quote) into xml:lang elements.
        if args.parse_languages:
            contents = re.sub(
                r'<quote>(\w{2,3})\s*:\s*',
                r'<quote xml:lang="\1">',
                contents)
            contents = re.sub(
                r'<foreignphrase>(\w{2,3})\s*:\s*',
                r'<foreignphrase xml:lang="\1">',
                contents)

        # Wrap the headings into Docbook sections. We need to first
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
        contents = self.wrap_sections(contents, args.root_element, 'h1',
            [ ])

        # If we are putting ID fields on the section 2 and 3's, then
        # we parse through it.
        contents = self.id_sections(contents)

        # Trim the space between the tags.
        contents = contents.replace('> <', '><')

        # After we wrap the sections, we can process the metadata if
        # requested. These are encoded as itemized lists right after
        # the <info> tags.
        if args.parse_metadata:
            metadata_parser = DocbookMetadataParser()
            contents = metadata_parser.parse(contents)

        # Parse the summary lines, if there are any of them.
        if args.parse_summaries:
            summary_parser = DocbookSummaryParser()
            contents = summary_parser.parse(contents)

        # Parse special paragraphs with prefix notations.
        if args.parse_special_paragraphs:
            paragraph_parser = DocbookParagraphParser()
            contents = paragraph_parser.parse(contents)

        # Strip out LocalWords paragraphs since this is a common
        # format for buffer- or file-specific dictionaries.
        if args.ignore_localwords:
            contents = re.sub(
                '<simpara[^>]*>LocalWords:.*?</simpara>',
                '',
                contents)

        # Combine blockquotes that are next to each other.
        contents = contents.replace('</blockquote><blockquote>', '')

        # Parse attributions inside blockquotes.
        if args.parse_attributions:
            attribution_parser = DocbookAttributionParser()
            contents = attribution_parser.parse(contents)
    
        # Add the namespaces and version to the top-level elements.
        # Add the XML and article headers.
        header_attributes = " ".join(namespaces)

        if args.id != None:
            header_attributes += ' id="' + args.id + '"'

        header_attributes += ' version="5.0"'

        contents = re.sub(
            '<' + args.root_element + '>',
            '<' + args.root_element + ' ' + header_attributes + '>',
            contents)
        contents = '<?xml version="1.0" encoding="UTF-8"?>' + contents

        # Remove the info tags, if we have blanks.
        contents = contents.replace('<info></info>', '')

        # In DocBook, list items have an inner paragraph instead of
        # just having a direct list item. This replaces those lists
        # with an inner paragraph.
        contents = re.sub(
            r'<listitem>(.*?)</listitem>',
            r'<listitem><para>\1</para></listitem>',
            contents)

        # Write the contents to the output file.
        output = open(output_filename, 'w')
        output.write(contents)
        output.write(os.linesep)
        output.close()

    def number_paragraphs(self, contents):
        """
        Goes through the contents and numbers every paragraph starting
        with the first one.
        """

        # Start by splitting on the paragraph tag but keeping the tag
        paragraphs = re.split('(<simpara>)', contents)

        # Through all the paragraphs and find the simple tags and
        # modify them in place.
        count = 1

        for index in range(len(paragraphs)):
            if paragraphs[index] == '<simpara>':
                paragraphs[index] = \
                    '<simpara mw:para-index="{0}">'.format(count)
                count = count + 1

        # Combine the resulting paragraphs back and return it
        return "".join(paragraphs)

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Creole to Docbook
        conversion.
        """

        super(CreoleDocbookConvertProcess, self).setup_arguments(parser)

        # Add the Creole-specific options.
        parser.add_argument(
            '--id',
            type=str,
            help='Assigns the id to the top-level generated DocBook element.')
        parser.add_argument(
            '--convert-quotes',
            action='store_true',
            help='Converts double quotes into Docbook <quote> elements.')
        parser.add_argument(
            '--enable-comments',
            action='store_true',
            help='If enabled, removes any lines that start with #.')
        parser.add_argument(
            '--ignore-localwords',
            action='store_true',
            help='Strips out paragraphs starting with LocalWords:')
        parser.add_argument(
            '--number-paragraphs',
            action='store_true',
            help='Numbers the paragraphs in the resulting XML.')
        parser.add_argument(
            '--parse-attributions',
            action='store_true',
            help='Parses attributions in blockquotes.')
        parser.add_argument(
            '--parse-backticks',
            action='store_true',
            help='Converts backticks (`phrase`) into foreigh phrases.')
        parser.add_argument(
            '--parse-languages',
            action='store_true',
            help='Converts language tags into xml:lang attributes.')
        parser.add_argument(
            '--parse-metadata',
            action='store_true',
            help='Processes itemized lists below headings as metadata.')
        parser.add_argument(
            '--parse-special-paragraphs',
            action='store_true',
            help="Parses special paragraph types into container objects.")
        parser.add_argument(
            '--parse-summaries',
            action='store_true',
            help="Parses the summary paragraphs as abstract tags.")
        parser.add_argument(
            '--root-element',
            default='article',
            choices=['article', 'chapter'],
            help="Determines the root element for converted files.")

    #
    # Sections
    #
    
    def id_sections(self, contents):
        """
        Give all the sections a unique identifier for the document.
        """

        # Split on the headings. The resulting list will have the initial
        # text in the first element, then pairs of elements for every
        # heading past it.
        section_index = 0
        section_regex = "<section>"
        sections = re.split(section_regex, contents)
        results = [sections[0]]
    
        # Loop through the resulting section pairs and create the elements.
        for index in range(1, len(sections)):
            results.append("<section id='s" + format(section_index) + "'>")
            results.append(sections[index])

            section_index += 1

        # Return the resulting sections.
        return "".join(results)

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
                log = logging.getLogger('wrap')
                log.warning('Skipping top section: ' + title)
                continue
    
            # Start by appending the section. We always include the
            # <info/> tag but we'll remove it later if it ends up
            # being blank.
            results.append('<' + element + '>')
            results.append('<info>')

            if len(title) > 0:
                results.append('<title>')
                results.append(title)
                results.append('</title>')

            results.append('</info>')
    
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


class DocbookAttributionParser(object):
    """Parses Creole data and generates attributed quotes."""

    REGEX = r'^(.*?)<blockquote>(.*?)</blockquote>(.*)$'

    log = logging.getLogger('attribution')

    def parse(self, contents):
        """
        Parses blockquotes looking for attributions and marks them as
        such.
        """

        # Keep track of all the components as we go through them.
        buf = []

        # Go through each itemized list right after an <info> tag in turn.
        search = re.search(
            self.REGEX,
            contents,
            re.MULTILINE)

        while search != None:
            # Save the first parts of the string as the contents
            # before the regex.
            buf.append(search.group(1))
            buf.append('<blockquote>')

            # Pull out the paragraphs and look for attributions. These
            # are identified as a special character followed by text,
            # but not ending with a paragraph.
            inner = search.group(2)
            inner_search = re.search(r'\s*&#8212;\s*([^<]+)</simpara>', inner)
            
            # If we found an attribute, use it.
            if inner_search != None:
                # Remove what we found from the inner contents.
                inner = inner.replace(inner_search.group(0), '')

                # Put the attribution before the paragraphs in the
                # blockquote. These are added with the
                # 'buf.append(inner)' line below.
                buf.append('<attribution>')
                buf.append(inner_search.group(1))
                buf.append('</attribution>')

            buf.append(inner)
            buf.append('</simpara>')

            # Finish the blockquote and put it on the buffer.
            buf.append('</blockquote>')

            # Finish by replacing the contents with the stuff after
            # the regex. This way, we only parse through a given
            # blockquote once.
            contents = search.group(3)

            # Look for the next match in the contents
            search = re.search(
                self.REGEX,
                contents,
                re.MULTILINE)

        # Return the resulting contents combined with the buffer so far.
        buf.append(contents)
        return "".join(buf)


class DocbookMetadataParser(object):
    """Processes Creole data to generate metadata."""

    # Regular Expressions
    METADATA_LIST_REGEX = (
        r'^(.*)</info><itemizedlist><listitem>\s*(.*?)\s*</listitem>'
        + r'</itemizedlist>(.*)$')
    METADATA_LIST_ITEM_REGEX = r'\s*</listitem><listitem>\s*'
    METADATA_ITEM_REGEX = r'(.*?)\s*:\s*(.*)$'

    log = logging.getLogger('metadata')

    def parse(self, contents):
        """
        Parses itemized lists right after the <info> tag and generates
        the appropriate metadata within the info tag.
        """

        # Go through each itemized list right after an <info> tag in turn.
        search = re.search(
            self.METADATA_LIST_REGEX,
            contents,
            re.MULTILINE)

        while search != None:
            # Save the first parts of the array
            buf = [search.group(1)]

            # Split apart the results and parse them as individual lines
            parts = re.split(self.METADATA_LIST_ITEM_REGEX, search.group(2))

            for metadata in parts:
                # Split out the line item as a colon-separated list
                split = re.match(self.METADATA_ITEM_REGEX, metadata)

                if split == None:
                    log = logging.getLogger('metadata')
                    log.error('Cannot parse metadata: ' + metadata)
                    continue

                # Figure out what to do based on the first element
                key = split.group(1)
                value = split.group(2)

                if key == 'Author':
                    buf.append(self.create_author(value))
                elif key == 'Copyright':
                    buf.append(self.create_copyright(value))
                else:
                    buf.append(self.create_subjectset(key, value))

            # Reconstruct the elements
            buf.append('</info>')
            buf.append(search.group(3))
            contents = "".join(buf)

            # Look for the next match in the contents
            search = re.search(
                self.METADATA_LIST_REGEX,
                contents,
                re.MULTILINE)

        # Look for subjectsets that need to be combined since they
        # have the same schema but potentially different tags.
        contents = re.sub(
            r'<subjectset schema="([^"]+)">(.*?)</subjectset>(.*?)'
            + r'<subjectset schema="\1">(.*?)</subjectset>',
            '<subjectset schema="\\1">\\2\\4</subjectset>\\3',
            contents)

        # Return the resulting contents
        return contents

    def create_author(self, value):
        """
        Create an <author> tag that represents the author string. The
        author string is "Last Name, First Name".
        """

        # Split on the comma for the name
        names = re.split(r'\s*,\s*', value)

        # Create the XML tag for the surname which we always
        # include. If we have a second name, we treat add it as the
        # first name.
        buf = ['<author><surname>', names[0], '</surname>']

        if len(names) > 1:
            buf.append('<firstname>')
            buf.append(names[1])
            buf.append('</firstname>')

        buf.append('</author>')

        # Return the resulting string.
        return "".join(buf)

    def create_copyright(self, value):
        """
        Create an <copyright> tag that represents the copryight. The
        string must be in the form of "Year[, Year], Author".
        """

        # Split on the comma for the name
        values = re.split(r'\s*,\s*', value)

        # Create the XML tag for the copyright.
        buf = ['<copyright>']

        # All but the last one is a year tag.
        for index in range(len(values)):
            if index == len(values) -1:
                buf.append('<holder>')
                buf.append(values[index])
                buf.append('</holder>')
            else:
                buf.append('<year>')
                buf.append(values[index])
                buf.append('</year>')

        buf.append('</copyright>')

        # Return the resulting string.
        return "".join(buf)

    def create_subjectset(self, key, value):
        """
        Create a subject XML fragment and return the results.
        """

        # Split on the semicolon for the subjectset. We need to escape the
        # character entities, if they exist, to avoid splitting on them.
        value = re.sub(r'(&#?\d+);', r'\1\tunicode\t', value)
        split_terms = re.split(r'\s*;\s*', value)

        # Create a fragment with the subject.
        terms = "</subjectterm></subject><subject><subjectterm>" \
            .join(split_terms)
        terms = terms.replace('\tunicode\t', ';')
        subject = "".join([
            '<subjectset schema="',
            key,
            '"><subject><subjectterm>',
            terms,
            "</subjectterm></subject></subjectset>"])
        
        # Return the resulting string
        return subject


class DocbookParagraphParser(object):
    """Parser for formatting special paragraphs from Creole."""

    PARA_REGEX = (
        r'^(.*)<simpara[^>]*>(NOTE|TIP|WARNING):'
        + r'\s*(.*?)</simpara>(.*)$')

    log = logging.getLogger('paragraph')

    def parse(self, contents):
        """
        Parses paragraphs for leading prefixes to identify their
        purpose. The following are used: NOTE, TIP, WARNING. Repeated
        blocks are combined into a single outer tag automatically.
        """

        # Go through each itemized list right after an <info> tag in turn.
        search = re.search(
            self.PARA_REGEX,
            contents,
            re.MULTILINE)

        while search != None:
            # Save the first parts of the string as the contents
            # before the regex.
            buf = [search.group(1)]

            # Create a container object, which is the second group in
            # lower case.
            buf.append('<')
            buf.append(search.group(2).lower())
            buf.append('><simpara>')

            # Add the contents of the paragraph
            buf.append(search.group(3))

            # Finish up the container tag.
            buf.append('</simpara>')
            buf.append('</')
            buf.append(search.group(2).lower())
            buf.append('>')

            # Finish up the string and put it back into the contents
            buf.append(search.group(4))
            contents = "".join(buf)

            # Look for the next match in the contents
            search = re.search(
                self.PARA_REGEX,
                contents,
                re.MULTILINE)

        # Merge multiple blocks of the same type together.
        types = ['note', 'tip', 'warning']

        for para_type in types:
            tags = "".join(['</', para_type, '><', para_type, '>'])
            contents = contents.replace(tags, '')

        # Return the resulting contents
        return contents


class DocbookSummaryParser(object):
    """Parses the text and create a DocBook summary."""

    SUMMARY_PARA_REGEX = (
        r'^(.*)</info><simpara[^>]*>SUMMARY:\s*(.*?)'
        + r'</simpara>(.*)$')

    log = logging.getLogger('summary')

    def parse(self, contents):
        """
        Parses the contents for summary lines. These are paragraphs that
        start with SUMMARY: and are merged into a single abstract.
        """

        # Go through each itemized list right after an <info> tag in turn.
        search = re.search(
            self.SUMMARY_PARA_REGEX,
            contents,
            re.MULTILINE)

        while search != None:
            # Save the first parts of the array
            buf = [search.group(1)]

            # Convert this into an abstract inside the <info> element.
            buf.append('<abstract><simpara>')
            buf.append(search.group(2))
            buf.append('</simpara></abstract>')
            buf.append('</info>')

            # Finish up the string and put it back into the contents
            buf.append(search.group(3))
            contents = "".join(buf)

            # Look for the next match in the contents
            search = re.search(
                self.SUMMARY_PARA_REGEX,
                contents,
                re.MULTILINE)

        # Merge multiple summary paragraphs (now abstracts) together.
        contents = contents.replace('</abstract><abstract>', '')

        # Return the resulting contents
        return contents
