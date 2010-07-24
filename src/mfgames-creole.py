#!/usr/bin/env python

#
# Documentation
#

#
# Imports
#

# System Imports
import argparse
import logging
import sys

# Local Imports
import mfgames.creole.docbook

#
# Constants
#

LOG_FORMAT = "%(asctime)-15s %(message)s"

#
# Processes
#

processes = {
    'docbook' : mfgames.creole.docbook.CreoleDocbookConvertProcess(),
    }

#
# Execution
#

def do_creole_tool(arguments):
    # Set up the primary parser.
    parser = argparse.ArgumentParser(
        description='Manipulate and convert Creole documents.')

    # Go through the processes and add each one's subparser.
    subparsers = parser.add_subparsers()

    for process_name, process in processes.iteritems():
        # Add this subparser to the primary parser.
        process_parser = subparsers.add_parser(
            process_name,
            help=process.help)
        process_parser.set_defaults(name=process_name)

        # Add the process-specific arguments to the parser.
        process.setup_arguments(process_parser)

    # Process the arguments given on the command line.
    args = parser.parse_args(arguments)

    # Set up the logging to use a common format.
    if args.log == None:
        logging.basicConfig(
            format = LOG_FORMAT,
            level = logging.DEBUG)
    else:
        logging.basicConfig(
            format = LOG_FORMAT,
            level = logging.DEBUG,
            filename = args.log)

    # Use the default to figure out the process name which is then
    # used to call the process() method in that Process class.
    selected_name = args.name
    selected_process = processes[selected_name]
    selected_process.process(args)

#
# Entry
#

if __name__ == "__main__":
    do_creole_tool(sys.argv[1:])
