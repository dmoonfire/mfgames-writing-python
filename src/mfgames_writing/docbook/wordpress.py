"""Uses DocBook to managed WordPress pages and sites."""


import codecs
import datetime
import logging
import lxml.etree
import mfgames_tools.process
import mfgames_writing.docbook.info
import os
import re
import sys
import time
import xml
import xmlrpclib


class UploadFilesProcess(mfgames_tools.process.InputFilesProcess):
    """Uploads files to a WordPress site, updating or adding pages as
    needed."""

    def __init__(self):
        # Let the base classes do what they need to do.
        super(UploadFilesProcess, self).__init__()

        # Keep track of the taxonomies we cached and their values.
        self.taxonomies = {}
        self.taxonomies_cached = []

    def get_help(self):
        return "Uploads files to a WordPress site."

    def pre_process_file(self):
        # Set up logging for the process.
        logging.basicConfig(
            format = "%(asctime)-15s %(message)s",
            level = logging.DEBUG)
        self.log = logging.getLogger('docbook-wordpress')

        # Load the stylesheet.
        xslt = lxml.etree.parse(self.args.xslt)
        self.transform = lxml.etree.XSLT(xslt)

        # Set up the XMLRPC proxy for this site.
        self.proxy = xmlrpclib.ServerProxy(self.args.url)

        # Retrieve all the pages on the website.
        self.get_options()
        self.cache_pages()
        self.cache_taxonomies()

        # Call the base implementation which will also process each
        # file.
        super(UploadFilesProcess, self).pre_process_file()

    def process_file(self, filename):
        # Parse the file as an XML object so we can pull out elements.
        xml = lxml.etree.parse(filename)

        # Strip off the common part of the root directory from the
        # filename, since this is the relative path inside the
        # WordPress site.
        abs_root_directory = (
            os.path.abspath(self.args.root_directory) + os.path.sep)
        abs_filename = os.path.abspath(filename)

        if not abs_filename.startswith(abs_root_directory):
            raise Exception("File does not appear in the root directory")

        # Get the relative filename for the WordPress site.
        rel_filename = abs_filename.replace(abs_root_directory, "")
        rel_filename = rel_filename.replace(".xml", "")

        # Get the hash of the file to determine if we need to change it.
        file_hash = mfgames_writing.get_file_hash(filename)

        # Figure out if the page exists already.
        if rel_filename in self.pages:
            self.update_page(
                filename, 
                rel_filename, 
                xml, 
                self.pages[rel_filename],
                file_hash)
        else:
            self.create_page(filename, rel_filename, xml, file_hash)

    def update_page(self, filename, rel_filename, xml, post, file_hash):
        # Pull out some useful variables.
        post = self.pages[rel_filename]
        post_id = post['post_id']

        # Check to see if the custom fields exists and if it matches.
        custom_fields = post['custom_fields']

        for custom_field in custom_fields:
            if custom_field['key'] == "mfgames-docbook-sha256":
                # If the value is the same, we don't change it.
                if not self.args.force and custom_field['value'] == file_hash:
                    self.log.info("Skipping because of hash: " + rel_filename)
                    return

                # Break out since we found what we're looking for.
                break

        # Report that we're creating a page.
        self.log.info("Updating page: " + rel_filename)

        # Create the content element for this page.
        content = self.get_wp_content(xml)

        # Add in the custom fields for the hash field.
        content['custom_fields'] = custom_fields
        found = False

        for custom_field in custom_fields:
            if custom_field['key'] == "mfgames-docbook-sha256":
                custom_field['value'] = file_hash
                found = True
                break

        if not found:
            custom_fields.append({
                    'key': "mfgames-docbook-sha256",
                    'value': file_hash,
                    })

        # Create the page on the server.
        self.proxy.wp.editPost(
            self.args.blog,
            self.args.username,
            self.args.password,
            post_id,
            content)

    def create_page(self, filename, rel_filename, xml, file_hash):
        # Report that we're creating a page.
        self.log.info("Creating page: " + rel_filename)

        # Use the relative filename to break out the component pages
        # since we have to calculate parent/child relationships.
        slugs = rel_filename.split(os.path.sep)

        # Get the parent and see if that exists.
        parent_path = "/".join(slugs[0:-1])

        if not parent_path in self.pages:
            self.log.error("  Cannot find parent page: " + parent_path)
            return

        # Create the content element for this page.
        content = self.get_wp_content(xml)
        content['post_name'] = slugs[-1]
        content['post_parent'] = self.pages[parent_path]['post_id']

        # Create the custom fields.
        custom_fields = [
            {"key": "mfgames-docbook-sha256", "value": file_hash},
            ]
        content['custom_fields'] = custom_fields

        # Create the page on the server.
        post_id = self.proxy.wp.newPost(
            self.args.blog,
            self.args.username,
            self.args.password,
            content)

        # Download the page and add it into the list.
        post = self.proxy.wp.getPost(
            self.args.blog,
            self.args.username,
            self.args.password,
            post_id)
        self.pages[rel_filename] = post

    def get_wp_content(self, xml):
        # Pull out the <info/> element.
        info = mfgames_writing.docbook.info._get_element_node(xml, "info", None)

        # If we got this far, we have to create the elements of the page.
        taxonomies = self.get_taxonomies(info)

        content = {
            'post_type': 'page',
            'post_status': 'publish',
            'post_title': self.get_title(info),
            'post_except': '',
            'post_content': self.get_content(xml),
            'terms_names': taxonomies,
            'comment_status': self.args.comments,
            }

        # Add the date, if we have one.
        date = self.get_date(info)

        if date:
            content['post_date_gmt'] = date

        # Return the resulting content object.
        return content

    def get_taxonomies(self, info):
        """Retrieves the custom taxonomies for the piece."""

        ns = mfgames_writing.docbook.info.docbook_lxml_ns
        subjectsets = {}

        for subjectset in info.getiterator(ns + "subjectset"):
            # Using the schema name, pull out the taxonomy.
            schema = subjectset.attrib['schema']

            # Check to see if we are excluding the taxonomies.
            if schema in self.args.exclude_taxonomy:
                continue

            # If we are including it and we can't find it, then report
            # it to the user.
            if not schema in self.taxonomies:
                self.log.warning("  Cannot find taxonomy: " + schema)
                continue
                               
            taxonomy_name = self.taxonomies[schema]['name']

            # Go through the child terms and build up a list of them.
            terms = []

            if taxonomy_name in subjectsets:
                terms = subjectsets[taxonomy_name]

            for subject in subjectset.getiterator(ns + "subject"):
                for subjectterm in subject.getiterator(ns + "subjectterm"):
                    term = subjectterm.text
                    terms.append(term)
            
            # Save the terms into the schema.
            subjectsets[taxonomy_name] = terms

        # Return the resulting terms.
        return subjectsets

    def get_content(self, xml):
        """Format and retrieves the contents of the piece."""

        # Process the results of the document.
        results = self.transform(xml)
        ns = mfgames_writing.docbook.info.docbook_lxml_ns
        xml_ns = mfgames_writing.docbook.info.xml_ns

        for div in results.xpath("/*", namespaces=xml_ns):
            contents = lxml.etree.tostring(div)
            contents = re.sub(r'^<div.*?>', '', contents)
            contents = re.sub(r'\s*</div>.*?$', '', contents, re.S)
            return contents

        # If we got this far, we don't know what to do.
        return None

    def get_title(self, info):
        """Retrieves the formatted title of the piece."""

        title = mfgames_writing.docbook.info._get_element_value(
            info, "title", "Unknown")
        subtitle = mfgames_writing.docbook.info._get_element_value(
            info, "subtitle", None)

        if subtitle:
            title += ": " + subtitle
        
        return title

    def get_date(self, info):
        """Retrieves the formatted date of the piece."""

        # Pull out the date field. If we don't have one, return none.
        date = mfgames_writing.docbook.info._get_element_value(
            info, "date", None)

        if not date:
            return None

        # Format the date field.
        xmldate = xmlrpclib.DateTime(
            datetime.datetime.strptime(date, "%Y-%m-%d"))
        return xmldate

    def get_options(self):
        """Retrieves a list of options from the server."""

        self.log.info("Getting options from the server")

        self.options = self.proxy.wp.getOptions(
            self.args.blog,
            self.args.username,
            self.args.password)

        # Break out some useful elements.
        self.blog_url = self.options['blog_url']['value']
        self.log.debug("  Using blog url: " + self.blog_url)

    def cache_taxonomies(self):
        """Downloads the master list of taxonomies from the server."""

        # Report what we're doing.
        self.log.debug("Downloading taxonomies")

        # We need to cache the basic taxonomy information.
        taxonomies = self.proxy.wp.getTaxonomies(
            self.args.blog,
            self.args.username,
            self.args.password)

        for taxonomy in taxonomies:
            # Add in the stubs for the terms.
            taxonomy['terms'] = {}

            # Get the name so we can save it.
            taxonomy_name = taxonomy['labels']['singular_name']
            self.taxonomies[taxonomy_name] = taxonomy

    def cache_pages(self):
        """Downloads a list of pages from the server so it can be cached."""

        # First start by retrieving the list of pages from the
        # server. We do that because with sites that have a lot of
        # pages, we can overload the server too easily.
        self.log.info("Downloading page list from server")

        pages = self.proxy.wp.getPageList(
            self.args.blog,
            self.args.username,
            self.args.password)

        self.log.info("Processing {0:n} pages".format(len(pages)))

        # Go through each post and retrieve it from the server.
        self.pages = {}

        next_report = int(time.time()) + 5
        processed = 0

        for page in pages:
            # Pull out information about the page.
            page_id = page['page_id']
            page_title = page['page_title']

            # Get the full page data
            data = self.proxy.wp.getPage(
                self.args.blog,
                page_id,
                self.args.username,
                self.args.password);
            data['post_id'] = page_id

            # Store the information about the page using the relative
            # link (without the blog_url).
            rel_link = data['link'].replace(self.blog_url, "")[1:]
            rel_link = re.sub(r'/$', "", rel_link)
            self.pages[rel_link] = data

            # DEBUG self.log.debug("Link {0}".format(rel_link))

            # Check to see if we need to report our status.
            processed += 1

            if (int(time.time()) > next_report):
                l = format(len(format(len(pages))))
                self.log.debug(
                    ("  Processed {2:5.1f}%: {0:" + l + "} of {1}").format(
                        processed,
                        len(pages),
                        100.0 * processed / len(pages)))
                next_report = time.time() + 60

    def setup_arguments(self, parser):
        # Add in the argument from the base class.
        super(UploadFilesProcess, self).setup_arguments(parser)

        # WordPress arguments
        parser.add_argument(
            '--url', '-l',
            type=str)
        parser.add_argument(
            '--user', '-U',
            type=str)
        parser.add_argument(
            '--pass', '-P',
            type=str)
        parser.add_argument(
            '--blog', '-B',
            type=str,
            default="")

        # Post preferences.
        parser.add_argument(
            '--comments',
            default='open',
            choices=['open', 'closed'])
        parser.add_argument(
            '--exclude-taxonomy',
            nargs='+')

        # Directory processing.
        parser.add_argument(
            '--root-directory', '-d',
            type=str,
            default=os.getcwd())

        # File processing
        parser.add_argument(
            '--xslt', '-x',
            type=str,
            default=None)
        parser.add_argument(
            '--force', '-f',
            default=False,
            action='store_true')


class GetPostProcess(mfgames_tools.process.Process):
    """Retrieves a single post and information about it from the server."""

    def __init__(self):
        super(GetPostProcess, self).__init__()

    def get_help(self):
        return "Downloads a post from a WordPress site."

    def process(self, args):
        # Call the base implementation which will also process each
        # file.
        super(GetPostProcess, self).process(args)

        # Set up logging for the process.
        logging.basicConfig(
            format = "%(asctime)-15s %(message)s",
            level = logging.DEBUG)
        self.log = logging.getLogger('docbook-wordpress')

        # Set up the XMLRPC proxy for this site.
        self.proxy = xmlrpclib.ServerProxy(args.url)

        # Get the page from the server.
        post = self.proxy.wp.getPost(
            self.args.blog,
            self.args.username,
            self.args.password,
            self.args.post)
        print post

    def setup_arguments(self, parser):
        # Add in the argument from the base class.
        super(GetPostProcess, self).setup_arguments(parser)

        # WordPress arguments
        parser.add_argument(
            '--url', '-l',
            type=str)
        parser.add_argument(
            '--user', '-U',
            type=str)
        parser.add_argument(
            '--pass', '-P',
            type=str)
        parser.add_argument(
            '--blog', '-B',
            type=str,
            default="")

        # Post
        parser.add_argument(
            'post',
            type=str)
