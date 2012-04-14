"""The various processes for querying and manipulating the Nav inside an NCX file."""


import codecs
import os
import sys
import xml

import tools.process
import writing.ncx


def get_navpoint_index(navpoints, id):
    index = 0

    for navpoint in navpoints:
        if navpoint[0] == id:
            return index

        index += 1

class NavAppendProcess(writing.ncx.ManipulateNcxFileProcess):
    """Appends a navigation entry to the NCX file."""

    def get_help(self):
        return "Appends a navigation entry to the NCX file."

    def manipulate(self):
        record = [
            self.args.id,
            self.args.title,
            self.args.href,
            ]
        self.ncx.navpoints.append(record)

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(NavAppendProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The unique identifier for the navigation point.")
        parser.add_argument(
            'title',
            type=str,
            help="The title for the navigation point.")
        parser.add_argument(
            'href',
            type=str,
            help="The href for the navigation entry.")

class NavInsertProcess(writing.ncx.ManipulateNcxFileProcess):
    """Inserts a navigation entry to the NCX file."""

    def get_help(self):
        return "Inserts a navigation entry to the NCX file."

    def manipulate(self):
        record = [
            self.args.id,
            self.args.title,
            self.args.href,
            ]

        index = get_navpoint_index(self.ncx.navpoints, self.args.before)
        self.ncx.navpoints.insert(self.args.before, record)

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(NavInsertProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'before',
            type=int,
            help="The unique identifier for the navigation point.")
        parser.add_argument(
            'id',
            type=str,
            help="The unique identifier for the navigation point.")
        parser.add_argument(
            'title',
            type=str,
            help="The title for the navigation point.")
        parser.add_argument(
            'href',
            type=str,
            help="The href for the navigation entry.")


class NavListProcess(writing.ncx.ReportNcxFileProcess):
    """Scans the NCX file and lists the nav entries."""

    def get_help(self):
        return "Lists the nav entries of a NCX."

    def report_tsv(self):
        index = 1
        for nav in self.ncx.navpoints:
            fields = [format(index), nav[0], nav[1], nav[2]]
            print('\t'.join(fields))
            index += 1


class NavRemoveProcess(writing.ncx.ManipulateNcxFileProcess):
    def get_help(self):
        return "Removes a given nav point."

    def manipulate(self):
        index = get_navpoint_index(self.ncx.navpoints, self.args.id)
        del self.ncx.navpoints[index]

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(NavRemoveProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'id',
            type=str,
            help="The unique identifier for the navigation point.")

