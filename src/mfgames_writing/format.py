"""Contains various formatting routines used by the tools."""


# Based on
# http://ginstrom.com/scribbles/2007/09/04/pretty-printing-a-table-in-python/


import locale


locale.setlocale(locale.LC_NUMERIC, "")


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def format_number(s, add_commas):
    """Format a number according to given places. Adds commas,
    etc. Will truncate floats into ints!"""

    # If we don't need to add commas, or the value isn't an integer,
    # then just return it as a string.
    if not add_commas or not is_number(s):
        return unicode(s)

    # Return the result as a formatting string.
    inum = int(s)
    return locale.format("%.*f", (0, inum), True)


def get_max_column_width(table, index, add_commas):
    """Get the maximum width of the given column index"""

    return max([len(format_number(row[index], add_commas)) for row in table])


def output_table(out, table, add_commas):
    """Prints out a table of data, padded for alignment
    @param out: Output stream (file-like object)
    @param table: The table to print. A list of lists.
    Each row must have the same number of columns. """

    # Gather up the width of each column in the table.
    column_widths = []

    for i in range(len(table[0])):
        column_widths.append(get_max_column_width(table, i, add_commas))

    # Go through the row and print out each column. This makes no
    # assumptions of which column has the text, but uses the field to
    # determine if this is right or left justified.
    for row in table:
        for i in range(0, len(row)):
            # Get the formatted value, with comma if requested.
            formatted = format_number(row[i], add_commas)

            # Figure out the column and use that to justify the
            # results.
            column_width = column_widths[i] + 2

            if is_number(row[i]):
                column = formatted.rjust(column_width)
            else:
                column = formatted.ljust(column_width)

            print >> out, column,
        print >> out
