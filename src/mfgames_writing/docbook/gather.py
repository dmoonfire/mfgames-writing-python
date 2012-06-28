"""Code to process a DocBook file and perform all requires inlining
and adjustment of paths and resources while copying them into a single
directory."""


import codecs
import logging
import mfgames_tools.process
import os
import shutil
import sys
import xml.sax
import xml.sax.saxutils


class _DocBookScanner(xml.sax.ContentHandler):
    """Scans a DocBook file and merges them into the appropriate output."""

    def __init__(self,
                 args,
                 input_filename, output_filename, output_stream,
                 is_included):
        xml.sax.ContentHandler.__init__(self)

        self.args = args
        self.log = logging.getLogger(os.path.basename(input_filename))
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.output_stream = output_stream
        self.input_directory = os.path.dirname(os.path.abspath(input_filename))
        self.output_directory = os.path.dirname(
            os.path.abspath(output_filename))

        # Some internal flags which are used to determine if we need
        # to strip out elements that should not be there. In specific,
        # DocBook says the version flag should not be on anything
        # besides the top-level element.
        self.is_included = is_included

        # If we are skipping elements, we need to keep track of how
        # much we're skipping. We do this with a depth counter that
        # will increment from zero and back down. When it is zero, we
        # aren't skipping anymore.
        self.skip = 0

    def characters(self, text):
        if self.skip > 0:
            return

        escaped = xml.sax.saxutils.escape(text)
        self.output_stream.write(escaped)

    def startDocument(self):
        # If we are not included, then prevent the <?xml?> from being
        # written out.
        if not self.is_included:
            xml.sax.ContentHandler.startDocument(self)

    def startElement(self, name, attrs):
        # Check to see if we are skipping elements.
        if self.skip > 0:
            # We are recursing into something, so skip it.
            self.skip += 1
            return

        # If we are an xinclude:include, then we recurse into the file
        # referenced instead of just copying it plainly. This is
        # effectively including all of the xinclude references.
        if name == "xinclude:include":
            # We are going to include a file.
            href = attrs["href"]
            include_filename = os.path.abspath(
                os.path.join(self.input_directory, href))

            # We have a file to include, so add it by creating a new
            # DocBookScanner that uses the same output file.
            self.log.info("Including file: " + href)

            # Create the parser with the output file and the current path.
            scanner = _DocBookScanner(
                self.args,
                include_filename,
                self.output_filename,
                self.output_stream, 
                True)
            parser = xml.sax.make_parser()
            parser.setContentHandler(scanner)
            parser.parse(include_filename)

            # We don't continue on, so return.
            return

        # If we have a media object, we start up the selector that
        # will pick the first one that we can use (and skip the ones
        # we can't and also skip the ones after).
        if name == "mediaobject":
            # If we are skipping media objects entirely, we need to check that.
            if self.args.strip_media == 'yes' or (
                self.args.strip_media == 'included-only' and
                self.is_included):
                # We are skipping this media object.
                self.skip = 1
                return

            # Reset the found object so we can find the first one.
            self.found_mediaobject = False

        if name == "imageobject" or name == "textobject":
            # Skip it if we found a media object. We need to skip all
            # of the elements underneath this, so we set the flag and
            # skip until we get to skip <= 0.
            if self.found_mediaobject and self.args.reduce_media:
                self.skip = 1
                return

            # Check to see if we have a condition, and if we do, then
            # skip items that do not match it.
            if self.args.filter_media:
                if not "condition" in attrs or not attrs["condition"] == self.args.filter_media:
                    # We either didn't have a condition or didn't match it.
                    self.skip = 1
                    return

            # Include this one, but mark it as the first found media object.
            self.found_mediaobject = True

        # Check for imagedata, which will be skipped if we aren't
        # processing it. If it is, then we need to copy the image
        # files over if requested.
        image_path = None

        if name == "imagedata" and self.args.copy_media:
            # The filename is located in fileref. We want to make it
            # an absolute path if it isn't already.
            fileref = attrs["fileref"]
            fileref = os.path.abspath(
                os.path.join(self.input_directory, fileref))
            baseref = os.path.basename(fileref)

            # Figure out where we are going to put the output file.
            outputref = os.path.abspath(
                os.path.join(self.args.media_directory, baseref))

            # Make sure the directory exists.
            output_directory = os.path.dirname(outputref)

            if not os.path.isdir(output_directory):
                self.log.info("Creating directory: " + output_directory)
                os.makedirs(output_directory)

            # Copy the file into the proper location.
            self.log.debug("Copying image from: " + fileref)
            shutil.copy(fileref, outputref)
            self.log.info("Copied image file: " + baseref)

            # Set up the image path so we can replace it.
            image_path = os.path.relpath(outputref, self.output_directory)

        # Write out a new element with modifications.
        self.output_stream.write("<");
        self.output_stream.write(name);

        # Go through and add all the attributes.
        for key in attrs.keys():
            # Pull out the value.
            value = attrs[key]

            # If we are included and there is a version, skip it.
            if self.is_included and key == "version":
                continue

            # Strip out known namespaces.
            if key == "xmlns:xinclude":
                continue

            if key == "xmlns" and self.is_included:
                continue

            # If this is an image reference, we need to replace it.
            if key == "fileref" and image_path:
                value = image_path

            # Write out the attribute.
            self.output_stream.write(" {0}=\"{1}\"".format(key, value))

        # Finish up the element
        self.output_stream.write(">");


    def endElement(self, name):
        # Check to see if we are skipping elements.
        if self.skip > 0:
            # We are recursing out of an element, so decrement the depth.
            self.skip -= 1
            return

        # If we are an xinclude:include, then we need to do something special.
        if name == "xinclude:include":
            # When we get this, we are done parsing the include file,
            # so just skip it.
            return

        # Just finish off the tag.
        self.output_stream.write("</{0}>".format(name))


class GatherFileProcess(mfgames_tools.process.InputFileProcess):
    """Primary process for gathering a file and all of its associated
    includes and resources."""

    def __init__(self):
        super(GatherFileProcess, self).__init__()

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(GatherFileProcess, self).process(args)

        # The gather process is somewhat verbose so we'll use a logger.
        log = logging.getLogger('gather')
        
        # If the path doesn't exist, then create it.
        if not os.path.exists(args.directory):
            log.info("Creating directory: " + args.directory)
            os.makedirs(args.directory)

        # Verify that the directory is not a file, since that will
        # cause problems.
        if not os.path.isdir(args.directory):
            log.error("The directory argument (" + args.directory +
                ") is not a directory")
            return

        # Figure out the name of the output file.
        if not args.output:
            args.output = os.path.join(
                args.directory,
                os.path.basename(args.file))

        # If the file exists and we are not overwritting, we have a problem.
        output_file = os.path.join(args.directory, args.output)

        if os.path.exists(args.output) and not args.force:
            log.error("Cannot overwrite file: " + output_file)
            return

        log.info("Using input file: " + args.file)
        log.info("Using output file: " + output_file)

        # Normalize the media directory, in case we use it.
        if not args.media_directory:
            args.media_directory = args.directory
        else:
            args.media_directory = os.path.join(
                args.directory, args.media_directory)

        # We have everything we need to perform the action. We create
        # an XML reader that will parse through this (and any
        # included) DocBook files and merge them into a single output
        # file. As we are parsing, we will optionally manipulate
        # elements and attributes as well as copying files as needed.

        # Open the output file.
        if args.output == "-":
            output = sys.stdout
        else:
            # We always use UTF-8 without BOM.
            output = codecs.open(args.output, 'w', 'utf-8')

        # Create the parser with the output file and the current path.
        scanner = _DocBookScanner(args, args.file, args.output, output, False)
        parser = xml.sax.make_parser()
        parser.setContentHandler(scanner)
        parser.parse(args.file)
        output.close()


    def setup_arguments(self, parser):
        """Sets up the command-line arguments for processing."""

        # Add in the argument from the base class.
        super(GatherFileProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'directory',
            type=str,
            help="Indicates the directory that the resources (e.g., images) will be copied to.")

        parser.add_argument(
            '--force', '-f',
            default=False,
            action='store_true',
            help="If set, overwrites files that exist in the output location.")
        parser.add_argument(
            '--output', '-o',
            type=str,
            help="The location to write out the source file. If this is excluded, then the output will be the same input file as the output.")
        parser.add_argument(
            '--reduce-media', '-r',
            default=False,
            action='store_true',
            help="If set, then mediaobjects (e.g., text, image) are reduced down to one.")
        parser.add_argument(
            '--filter-media', '-m',
            type=str,
            help="If set, then the condition element on a imageobject must match for it to be included.")
        parser.add_argument(
            '--strip-media',
            type=str,
            default='no',
            choices=['no', 'yes', 'included-only'],
            help="If 'no', then no stripping. If 'yes', all media will be stripped. If 'included-only', then only media in included files will be stripped.")
        parser.add_argument(
            '--copy-media', '-c',
            default=False,
            action='store_true',
            help="If included, then image files will be copied in the output directory.")
        parser.add_argument(
            '--media-directory',
            type=str,
            help="If set, then media files will be copied here instead of the output. This can be a relative path to the output directory.")

    def get_help(self):
        return "Merges a DocBook file and all includes and gathers up external resources such as images."
