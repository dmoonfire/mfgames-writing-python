# Contains the libraries and functions common to all the tools that
# convert from one (or more) files into another format.

#
# Imports
#

# System Imports
import argparse
import logging
from os.path import exists, split, splitext, join

# Internal Imports
import mfgames.process

#
# Convert Process
#

class ConvertProcess(mfgames.process.Process):
    def process(self, args):
        """
        Performs the actions on the given arguments.
        """

        # Verify the parameters. The 'output' option cannot be used with
        # multiple files. The 'output' is also exclusive of the
        # 'directory' and 'extension' options.
        if args.files == 0:
            log.exception('No files to docbook were given.')
            return

        if args.output and len(args.files) != 1:
            log.exception('The --output option cannot be used with more '
                + 'than one file.');
            return

        # If we are using the output, just use that for the output filename
        # and don't bother looping since we know there is exactly one file.
        if args.output:
            # Convert a single file with the given filename.
            self._convert_file(args, files[0], args.output)
        else:
            # Convert all the outputs, mapping the output as needed.
            for filename in args.files:
                # Figure out the various parts of the filename so it can
                # be reconstructed with the extensions.
                split_parts = split(filename)
                ext_parts = splitext(split_parts[1])

                # Determine the output directory which will either be the
                # same directory as the input or the directory given in
                # the arguments.
                dirname = split_parts[0]

                if args.directory:
                    dirname = args.directory
  
                # Figure out the output file, which is the base name of
                # the file plus the conversion-specific extension (as
                # defined by the convert_extension default).
                ext = self.get_extension()
                output_filename = join(dirname, ext_parts[0] + '.' + ext)
 
                # Pass the converted file to the conversion routine.
                self._convert_file(args, filename, output_filename)
            # end for
       # end if
    # end process

    def get_extension(self):
        """
        Gets the default extension to create output files.
        """

        raise Exception('Derived class does not define get_extension()')

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for a convert process.
        """

        # Set up the options for conversions.
        parser.add_argument(
            '-d', '--directory',
            help='The output directory to create the files. This will flatten the file structure and removes relative directory trees. If omitted, this will create the output files in the same directory as the input.')
        parser.add_argument(
            '-e', '--extension',
            help='The extension to use. If not specified, uses format-specific.')
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='If set, replace the output file even if it already exists.')
        parser.add_argument(
            '-o', '--output',
            type=argparse.FileType('w'),
            help='The output of the conversion. This may only be used with a single file.')

        # We use the 'str' instead of the FileType since we will be
        # opening these files in many cases.
        parser.add_argument(
            'files',
            metavar='file',
            type=str,
            nargs='+',
            help='Creole files to docbook.')

    #
    # Conversion
    #

    def _convert_file(self, args, input_filename, output_filename):
        """Converts a single file into another file."""

        # Set up logging for the function.
        log = logging.getLogger('convert')
        log.info("Converting " + input_filename)
        log.debug('Output ' + output_filename)

        # If the output file exists, then either warn or keep going.
        if not args.force and exists(output_filename):
            log.error('Output file exists, not converting ' + input_filename)
            return

        # Convert the input file into the output file.
        self.convert_file(args, input_filename, output_filename)

    def convert_file(self, args, input_filename, output_filename):
        raise Exception('Derived class does not extend convert_file()')
