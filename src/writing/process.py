import abc
import logging
import os


class ProcessError(Exception):
    """Exception thrown when there is an error in a process."""
    pass


class Process(object):
    __metaclass__ = abc.ABCMeta

    """Defines the top-level process object used by the script tasks.

    The Process class is the base class for all the tasks for the
    scripts. Each action, such as "convert to creole" or "extract
    subjects" are all individual processes within the system.

    The two primary functions in the class are:
        setup_arguments(self, parser)
            Sets up the arguments parser for the entire process. This
            should always call the super for the class to ensure
            common arguments are included.

        process(self, args)
            This performs the actual process. The args object passed
            in is the argument object setup by the setup_arguments
            method. Extending classes should class super before any
            processing of their own.
    """

    def process(self, args):
        """Performs the process on the input arguments."""
        pass

    def setup_arguments(self, parser):
        """Creates the parser object for the process."""

        # All processes have the controls for logging.
        parser.add_argument(
            "--log",
            type=str,
            help="If set, the output for logging goes to the given filename.")


class InputFilesProcess(Process):
    """Defines a process that takes one or more files.

    An input file process takes one or more files and ensures that all
    of them exist as part of the process verification.
    """

    def process(self, args):
        """Verifies the input files exist."""

        # Make sure at least one file is provided.
        if args.files == 0:
            raise ProcessError("No input files were provided.")

        # Ensure that all the files exists.
        for filename in args.files:
            if not os.path.exists(filename):
                raise ProcessError("Cannot find input file: " + filename)

    def setup_arguments(self, parser):
        """Sets up the arguments to handle file inputs."""

        # Call the base implementation for the common arguments.
        super(InputFilesProcess, self).setup_arguments(parser)
        
        # We use the 'str' instead of the FileType since the file will be
        # opened with unicode support or another reason.
        parser.add_argument(
            'files',
            metavar='file',
            type=str,
            nargs='+',
            help='Files to be processed by the action.')


class ConvertFilesProcess(InputFilesProcess):
    """Converts a set of files from one format to another."""

    def process(self, args):
        """
        Performs the actions on the given arguments.
        """

        # Call the base implementation for the common arguments.
        super(ConvertFilesProcess, self).process(args)
        
        # Verify the parameters. The 'output' option cannot be used with
        # multiple files.
        if args.output and len(args.files) != 1:
            raise ProcessError(
                'The --output option cannot be used with more '
                + 'than one file.');

        # If we are using the output, just use that for the output filename
        # and don't bother looping since we know there is exactly one file.
        if args.output:
            # Convert a single file with the given filename.
            self.safe_convert_file(args, args.files[0], args.output)
        else:
            # Convert all the outputs, mapping the output as needed.
            for filename in args.files:
                # Figure out the various parts of the filename so it can
                # be reconstructed with the extensions.
                split_parts = os.path.split(filename)
                ext_parts = os.path.splitext(split_parts[1])

                # Determine the output directory which will either be the
                # same directory as the input or the directory given in
                # the arguments.
                dirname = split_parts[0]

                if args.directory:
                    # Start with the base directory name from the parameter.
                    dirname = args.directory

                    # If we have a relative root, then the relative
                    # directories from the input file.
                    if args.relative_root != None:
                        # Create the relative directory by removing
                        # the relative root, strip off the leading
                        # directory separator character, and join it
                        # with the directory already parsed.
                        relative = split_parts[0]
                        relative = relative.replace(args.relative_root, '')
                        relative = relative[1:]
                        dirname = os.path.join(dirname, relative)

                    # Create the directories if needed.
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
  
                # Figure out the output file, which is the base name of
                # the file plus the conversion-specific extension (as
                # defined by the convert_extension default).
                ext = self.get_extension()
                output_filename = os.path.join(
                    dirname,
                    ext_parts[0] + '.' + ext)
 
                # Pass the converted file to the conversion routine.
                self.safe_convert_file(args, filename, output_filename)

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for a convert process.
        """

        # Add the base arguments.
        super(ConvertFilesProcess, self).setup_arguments(parser)

        # Set up the options for conversions.
        parser.add_argument(
            '-d', '--directory',
            help=(
                'The output directory to create the files. This will flatten '
                + 'the file structure and removes relative directory trees. '
                + 'If omitted, this will create the output files in the same '
                + 'directory as the input.'))
        parser.add_argument(
            '-e', '--extension',
            help=('The extension to use. If not specified, uses '
                  + 'format-specific.'))
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='If set, replace the output file even if it already exists.')
        parser.add_argument(
            '-o', '--output',
            type=str,
            help=('The output of the conversion. This may only be used '
                  + 'with a single file.'))
        parser.add_argument(
            '--relative-root',
            type=str,
            help=('If defined, then the given value will be stripped '
                  + 'from the input filenames and the resulting relative '
                  + 'path will be used with the --directory option.'))

    @abc.abstractmethod
    def get_extension(self):
        """Gets the default extension to create output files."""
        pass

    def safe_convert_file(self, args, input_filename, output_filename):
        """Safely converts an input file into an output file."""

        # Set up logging for the function.
        log = logging.getLogger('convert')
        log.info("Converting " + input_filename)
        log.debug('Output ' + output_filename)

        # If the output file exists, then either warn or keep going.
        if not args.force and os.path.exists(output_filename):
            raise ProcessError(
                'Output file exists, not converting ' + input_filename)
            return

        # Convert the input file into the output file.
        self.convert_file(args, input_filename, output_filename)

    @abc.abstractmethod
    def convert_file(self, args, input_filename, output_filename):
        """Converts a single file into another format."""
        pass
