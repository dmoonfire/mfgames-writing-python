import logging
import mfgames_tools.process
import xml.sax
import xml.sax.saxutils
import os


class _DependsScanner(xml.sax.ContentHandler):
    def __init__(self, args, filename):
        # Initialize the class.
        xml.sax.ContentHandler.__init__(self)

        # Save the simple variables in the class.
        self.filename = filename
        self.args = args

        # Gather up all the names into a variable.
        self.depends = []

        # Get the input file with the appropriate relative root.
        self.rel_filename = filename

        if args.directory_root:
             abs_filename = os.path.abspath(filename)
             abs_root = os.path.abspath(args.directory_root)
             self.rel_filename = os.path.relpath(abs_filename, abs_root)

        if args.directory_prefix:
            self.rel_filename = os.path.join(
                args.directory_prefix,
                self.rel_filename)

    def startElement(self, name, attrs):
        if name == "xinclude:include" and not self.args.no_xinclude:
            href = attrs["href"]
            self.report(href)

        if name == "imagedata" and not self.args.no_images:
            fileref = attrs["fileref"]
            self.report(fileref)

    def report(self, path):
        """Reports the path to the user."""

        # If we have a relative root, we want to show the full path.
        if self.args.directory_root:
            # Figure out what the absolute path of the included file would be.
            root_path = os.path.abspath(self.filename)
            root_directory = os.path.dirname(root_path)
            abs_path = os.path.join(root_directory, path)

            # Remove the root from this and set the path to that relative root.
            path = os.path.relpath(abs_path, self.args.directory_root)

        # Figure out if we need a directory prefix.
        if self.args.directory_prefix:
            path = os.path.join(self.args.directory_prefix, path)

        # Add the dependencies to the list.
        self.depends.append(path)


class DependsFileProcess(mfgames_tools.process.InputFileProcess):
    def __init__(self):
        super(DependsFileProcess, self).__init__()

    def process(self, args):
        # Handle the base class' processing which verifies the file
        # already exists.
        super(DependsFileProcess, self).process(args)

        # The gather process is somewhat verbose so we'll use a logger.
        log = logging.getLogger('depends')
        
        # Create the parser with the output file and the current path.
        scanner = _DependsScanner(args, args.file)
        parser = xml.sax.make_parser()
        parser.setFeature(
            "http://xml.org/sax/features/external-general-entities",
            False)
        parser.setContentHandler(scanner)
        parser.parse(args.file)

        # Once we are done, figure out how to format it.
        depends = scanner.depends

        if self.args.format == 'list':
            print "\n".join(depends)

        if self.args.format == "makefile":
            filename = scanner.rel_filename

            if args.makefile_prefix:
                filename += " {0}".format(args.makefile_prefix)

            print "{0}: {1}".format(filename, " ".join(depends))


    def setup_arguments(self, parser):
        # Add in the argument from the base class.
        super(DependsFileProcess, self).setup_arguments(parser)

        parser.add_argument(
            '--directory-root', '-d',
            default=None)
        parser.add_argument(
            '--directory-prefix', '-p',
            default=None)
        parser.add_argument(
            '--format', '-f',
            choices=['list', 'makefile'],
            default='list')
        parser.add_argument(
            '--makefile-prefix',
            default=None)

        parser.add_argument(
            '--no-xinclude', '-x',
            default=False,
            action="store_true")
        parser.add_argument(
            '--no-images', '-i',
            default=False,
            action="store_true")

    def get_help(self):
        return "Lists all the depends files."
