#
# Imports
#

# System Imports
import argparse
import logging

# Internal Imports
import mfgames.constants
import mfgames.convert
import mfgames.process

#
# Conversion Class
#

class DocbookCreoleConvertProcess(mfgames.convert.ConvertProcess):
    help = 'Converts Docbook 5 files into Creole.'
    log = logging.getLogger('creole')

    def get_extension(self):
        return "txt"

    def convert_file(self, args, input_filename, output_filename):
        """
        Converts the given file into Creole.
        """
    
    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the Docbook to Creole
        conversion.
        """

        super(DocbookCreoleConvertProcess, self).setup_arguments(parser)
