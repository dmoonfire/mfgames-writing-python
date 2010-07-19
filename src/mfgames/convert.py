# Contains the libraries and functions common to all the tools that
# convert from one (or more) files into another format.

#
# Imports
#

# System Imports
import argparse
import logging
from os.path import exists, split, splitext, join

#
# Arguments
#

def setup_convert(parser):
    """
    Adds the common arguments for all conversion routines.

    This assumes that convert_function, convert_extension functions
    are all set in the subparser's defaults.
    """

    # Set up the callback function.
    parser.set_defaults(function=convert_files)

    # Arguments to the conversion routines.
    parser.add_argument(
        '-d', '--directory',
        help='The output directory to create the files. This will flatten the file structure and removes relative directory trees. If omitted, this will create the output files in the same directory as the input.')
    parser.add_argument(
        '-e', '--extension',
        help='The extension to use. If not specified, uses format-specific.')
    parser.add_argument(
        '-f', '--force',
        help='If set, replace the output file even if it already exists.')
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w'),
        help='The output of the conversion. This may only be used with a single file.')

    # We use the 'str' instead of the FileType since we will be
    # opening these files in utf-8 universally.
    parser.add_argument(
        'files',
        metavar='file',
        type=str,
        nargs='+',
        help='Creole files to docbook.')

#
# Conversion
#

def convert_file(args, input_filename, output_filename):
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
    args.convert_function(args, input_filename, output_filename)

def convert_files(args):
    """Processes the arguments and converts the files."""

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
        convert_file(args, files[0], args.output)
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
            ext = args.convert_extension()
            output_filename = join(dirname, ext_parts[0] + '.' + ext)

            # Pass the converted file to the conversion routine.
            convert_file(args, filename, output_filename)
        # end for
    # end if
