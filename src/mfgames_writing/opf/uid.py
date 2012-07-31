"""The various processes for querying and manipulating the UID inside an OPF file."""


import codecs
import mfgames_writing.opf
import os
import sys
import uuid
import xml


class UidGetProcess(mfgames_writing.opf.ReportOpfFileProcess):
    """Scans the OPF file and gets the UID entries."""

    def get_help(self):
        return "Gets the UID entries of a OPF."

    def report_tsv(self):
        # The UID actually points to a dc:identifier with the name id field.
        uid_id = self.opf.uid_id

        if not uid_id:
            print("<NONE>")
            return

        # Dereference the variable using the id attribute.
        key = "identifier#" + uid_id

        if not key in self.opf.metadata_dc:
            print("<The uuid ID " +
                  uid_id + " could not be found in the dc metadata>")
            return

        # We have a valid field, so use that.
        uid = self.opf.metadata_dc[key]
        fields = [ uid ]
        print('\t'.join(fields))


class UidSetProcess(mfgames_writing.opf.ManipulateOpfFileProcess):
    """Sets the uid to a manifest entry."""

    def get_help(self):
        return "Sets the given uid to an item in the manifest."""

    def manipulate(self):
        # The UID is actually a deferenced variable. We need to first
        # figure outwhat the ID field would be.
        uid_id = self.opf.uid_id

        if not uid_id:
            # We don't have one yet, so use a "sane" default and set
            # it in the internal variable along with keeping it for
            # the lookup key below.
            uid_id = "uid"
            self.args.uid_id

        # Set the Dublin Core metadata using the key we identified.
        key = "identifier#" + uid_id

        self.opf.metadata_dc[key] = self.args.uid

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for file processing."""

        # Add in the argument from the base class.
        super(UidSetProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            'uid',
            type=str,
            help="The new identifier for the OPF")


class UidGenerateProcess(mfgames_writing.opf.ManipulateOpfFileProcess):
    """Sets the unique identifier of an OPF file to a new UUID."""

    def get_help(self):
        return "Generates a new UUID for an OPF file."""

    def manipulate(self):
        # The UID is actually a deferenced variable. We need to first
        # figure outwhat the ID field would be.
        uid_id = self.opf.uid_id

        if not uid_id:
            # We don't have one yet, so use a "sane" default and set
            # it in the internal variable along with keeping it for
            # the lookup key below.
            uid_id = "uid"
            self.opf.uid_id = uid_id

        # Make sure the unique identifier is defined.
        key = "identifier#" + uid_id

        if key not in self.opf.metadata_dc or not self.opf.metadata_dc[key] or self.args.force:
            uid = uuid.uuid4()
            self.opf.metadata_dc[key] = "urn:uuid:" + uid.hex

    def setup_arguments(self, parser):
        # Add in the argument from the base class.
        super(UidGenerateProcess, self).setup_arguments(parser)

        # Add in the text-specific generations.
        parser.add_argument(
            '--force', '-f',
            default=False,
            action='store_true',
            help="If set, then always generate a new UID.")

