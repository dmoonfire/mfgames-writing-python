#!/usr/bin/python


"""This program goes through an input file and shows the first five
lines of every sentence. This makes the assumption that the input file
has one paragraph per line and is in a text file."""


import fileinput
import re


def process():
    # Go through all the lines in the input until we get to the end of the file.
    line_index = 0
    
    for line in fileinput.input():
        # Increment the line number for output.
        line_index += 1
        
        # Ignore commented lines.
        if line.startswith("#"):
            continue
        
        # Clean up the line of whitespace. This makes it easier to parse
        # the lines.
        line = line.strip()
        
        # If the line is blank, then jsut output a line break.
        if line == "":
            print
            continue

        # First split the line on the periods. It isn't perfect, but
        # should give a rough sentence start.
        sentences = re.split(r'\.', line)
        counts = []
        
        for sentence in sentences:
            # Ignore blanks sentences since Python returns the final "."
            # as a blank.
            sentence = sentence.strip()
            
            if sentence == "" or sentence == "\"":
                continue

            # For each sentence, we split apart the spaces to get the words.
            words = re.split(r'\s+', sentence)
            
            # Figure out how many words are in the sentence.
            count = len(words)
            counts.append(count)

            # We only care about teh first five words in the sentence.
            prefix = words[0:5]

            # Print out the sentence and its length. We also include the
            # line number so we can easily jump to that line.
            print "{0}: {1} ({2})".format(
                line_index,
                " ".join(prefix),
                count)
            
        # Calculate the std. dev for the counts. If there is a small
        # average, then we have too much of a consistence sentence length.
            
        # Put in a summary for the paragraph.
        sd = stddev(counts)
            
        if sd > 0:
            print "-- {0} sentences, {1:.1f} median, {2:.1f} stddev".format(
                len(counts),
                median(counts),
                sd)
                

def median(args):
    total = sum(args)
    average = float(total)/len(args)
    return average


def stddev(args):
    # StdDev doesn't mean anything with no elements, so just return 0.
    if len(args) <= 1:
        return 0 

    # Figure out the median value.
    average = median(args)

    # Figure out the total of the squares differences from the median.
    total = 0

    for value in args:
        total += (average - float(value)) ** 2

    # Calculate the StdDEv and return it.
    stddev = (total / (len(args) - 1)) ** 0.5
    return stddev


process()
