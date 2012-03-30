"""The various processes for querying and manipulating the Nav inside an NCX file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.ncx


class NavListProcess(writing.ncx.ReportNcxFileProcess):
    """Scans the NCX file and lists the nav entries."""

    def get_help(self):
        return "Lists the nav entries of a NCX."

    def report_tsv(self):
        index = 1
        for nav in self.ncx.navpoints:
            fields = [nav[0], nav[1], nav[2]]
            print('\t'.join(fields))
            index += 1


# class NavRemoveProcess(writing.ncx.ManipulateNcxFileProcess):
#     def get_help(self):
#         return "Removes a given nav fields."

#     def manipulate(self):
#         #self.ncx.navdata_dc[self.args.key] = self.args.value
#         pass

#     def setup_arguments(self, parser):
#         """Sets up the command-line arguments for file processing."""

#         # Add in the argument from the base class.
#         super(NavRemoveProcess, self).setup_arguments(parser)

#         # Add in the text-specific generations.
#         parser.add_argument(
#             'key',
#             type=str,
#             help="The Nav field, without the leading dc: (e.g., Creator)")


# class NavSetProcess(writing.ncx.ManipulateNcxFileProcess):
#     """Scans the NCX file and lists the nav entries."""

#     def get_help(self):
#         return "Sets the given nav field to the given value."

#     def manipulate(self):
#         self.ncx.nav[self.args.key] = self.args.value

#     def setup_arguments(self, parser):
#         """Sets up the command-line arguments for file processing."""

#         # Add in the argument from the base class.
#         super(NavSetProcess, self).setup_arguments(parser)

#         # Add in the text-specific generations.
#         parser.add_argument(
#             'key',
#             type=str,
#             help="The nav field, including any namespace such as dtd:")
#         parser.add_argument(
#             'value',
#             type=str,
#             help="The value for the field.")

