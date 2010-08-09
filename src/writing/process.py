#
# Process
#

class Process(object):
    def process(self, args):
        """
        Performs the actions on the given arguments.
        """

        raise Exception('Derived class did not extend process()')

    def setup_arguments(self, parser):
        """
        Sets up the command-line arguments for the process.
        """

        parser.add_argument(
            "--log",
            type=str,
            help="If set, the output for logging goes to the given filename.")

