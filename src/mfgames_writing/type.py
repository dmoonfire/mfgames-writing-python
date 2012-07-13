"""
Parsing module for taking a DocBook string to create typographical
quotes.
"""

import re


OPEN_DOUBLE_QUOTE = u'\u201C'
CLOSE_DOUBLE_QUOTE = u'\u201D'
OPEN_SINGLE_QUOTE = u'\u2018'
CLOSE_SINGLE_QUOTE = u'\u2019'
EN_DASH = u'\u2013'
EM_DASH = u'\u2014'
ELLIPSIS = u'\u2026'

QUOTE_CHARACTERS = [
    "'", '"', '`',
    OPEN_DOUBLE_QUOTE,
    CLOSE_DOUBLE_QUOTE,
    OPEN_SINGLE_QUOTE,
    CLOSE_SINGLE_QUOTE,
    ]
DOUBLE_QUOTE_CHARACTERS = [
    '"', 
    OPEN_DOUBLE_QUOTE,
    CLOSE_DOUBLE_QUOTE]
SINGLE_QUOTE_CHARACTERS = [
    "'", 
    OPEN_SINGLE_QUOTE,
    CLOSE_SINGLE_QUOTE]
TICK_QUOTE_CHARACTERS = ["`"]

PUNCT_CHARACTERS = [".", ",", "!", "?", ":", ";"]

OUTSIDE = 0
IN_DOUBLE = 1
IN_SINGLE = 2
IN_TICK = 3

SIGNIFICANT = 0
INSIGNIFICANT = 1
INDETERMINATE = 2

NORMAL_TOKEN = 0
QUOTE_TOKEN = 1
TERMINAL_TOKEN = 2

class TypographicalConvertor(object):
    """Base class for converting quote strings into their
    typographical reprsentations. This allows a pluggable interface
    that lets the calling application to determine how they are placed
    into there."""

    def __init__(self):
        super(TypographicalConvertor, self).__init__()
        self.use_unicode()

    def use_ascii(self):
        """Sets the various rendering elements to use Unicode glyphs."""

        self.apostrophe = "'"
        self.close_double_quote = '"'
        self.close_ended_double_quote = ""
        self.close_ended_single_quote = ""
        self.close_ended_tick_quote = ""
        self.close_single_quote = "'"
        self.close_tick_quote = "`"
        self.ellipsis = "..."
        self.em_dash = "---"
        self.en_dash = "--"
        self.open_double_quote = '"'
        self.open_ended_double_quote = '"'
        self.open_ended_single_quote = "'"
        self.open_ended_tick_quote = '`'
        self.open_single_quote = "'"
        self.open_tick_quote = "`"

    def use_unicode(self):
        """Sets the various rendering elements to use Unicode glyphs."""

        self.apostrophe = CLOSE_SINGLE_QUOTE
        self.close_double_quote = CLOSE_DOUBLE_QUOTE
        self.close_ended_double_quote = ""
        self.close_ended_single_quote = ""
        self.close_ended_tick_quote = ""
        self.close_single_quote = CLOSE_SINGLE_QUOTE
        self.close_tick_quote = "`"
        self.ellipsis = ELLIPSIS
        self.em_dash = EM_DASH
        self.en_dash = EN_DASH
        self.open_double_quote = OPEN_DOUBLE_QUOTE
        self.open_ended_double_quote = OPEN_DOUBLE_QUOTE
        self.open_ended_single_quote = OPEN_SINGLE_QUOTE
        self.open_ended_tick_quote = "`"
        self.open_single_quote = OPEN_SINGLE_QUOTE
        self.open_tick_quote = "`"

    def convert(self, input_string):
        # Pull out the tokens from the input string.
        tokens = self.tokenize(input_string)

        # Go through the tokens and produce an array of output tokens.
        self.state = [OUTSIDE]
        self.quote_index = 0
        self.output = []
        self.quotes = []

        for index in range(len(tokens)):
            # Get the token results.
            results, token_type = self.process_token(tokens, index)

            # If this is a quote, we need to add it to the list.
            if token_type == QUOTE_TOKEN:
                self.quotes.append(len(self.output))

            # If we have a terminal token, then we need to close any
            # open quotes.
            if token_type == TERMINAL_TOKEN:
                self.close_quotes()

            # Add the token to the output.
            self.output.append(results)

        # Finish off any quotes we had.
        self.close_quotes()

        # Return the resulting output.
        output_string = "".join(self.output)
        return output_string

    def close_quotes(self):
        """Closes any open quotes we have in the current buffer."""

        # If we have remaining elements in the state (besides the
        # first), we need to convert the quotes to open-ended and
        # finish off the tags.
        while len(self.state) > 1:
            quote_type = self.state.pop()
            quote_index = self.quotes.pop()

            if quote_type == IN_DOUBLE:
                self.output[quote_index] = self.open_ended_double_quote
                self.output.append(self.close_ended_double_quote)
            elif quote_type == IN_SINGLE:
                self.output[quote_index] = self.open_ended_single_quote
                self.output.append(self.close_ended_single_quote)
            elif quote_type == IN_TICK:
                self.output[quote_index] = self.open_ended_tick_quote
                self.output.append(self.close_ended_tick_quote)

    def process_token(self, tokens, index):
        """Processes a token in the token list and returns an output
        token to append to the output."""

        token = tokens[index]
        state = self.state[-1]

        # Check for double quotes, which are pretty simple since they
        # rarely show up outside of quote.
        if token in DOUBLE_QUOTE_CHARACTERS:
            if state == IN_DOUBLE:
                self.state.pop()
                return self.close_double_quote, NORMAL_TOKEN
            else:
                self.quote_index += 1
                self.state.append(IN_DOUBLE)
                return self.open_double_quote, QUOTE_TOKEN
        
        # Single quotes are a heavily used in English. In specific, if
        # they are following a significant tokens (e.g., text), then
        # it is an abbreviation. Otherwise, it is a nested quote.
        if token in SINGLE_QUOTE_CHARACTERS:
            if state == IN_SINGLE:
                # This is closing a single quote.
                self.state.pop()
                return self.close_single_quote, NORMAL_TOKEN

            if self.is_preceding_significant(tokens, index):
                # This is an apostrophe character.
                return self.apostrophe, NORMAL_TOKEN
            
            # Otherwise, we are opening a new quote.
            self.quote_index += 1
            self.state.append(IN_SINGLE)
            return self.open_single_quote, QUOTE_TOKEN

        if token in TICK_QUOTE_CHARACTERS:
            if state == IN_TICK:
                self.state.pop()
                return self.close_tick_quote, NORMAL_TOKEN
            else:
                self.quote_index += 1
                self.state.append(IN_TICK)
                return self.open_tick_quote, QUOTE_TOKEN

        # For all other tokens, just return the token.
        return token, False

    def is_preceding_significant(self, tokens, index):
        """Determines if the preceding token is significant."""

        # If we started at the beginning, we are never significant.
        if index == 0:
            return False

        # Get the previous token and figure out how significant it is.
        previous_token = tokens[index - 1]
        significance = self.get_significance(previous_token)

        if significance == SIGNIFICANT:
            # This is explictly significant.
            return True
        elif significance == INSIGNIFICANT:
            # This is explictly insignificant.
            return False
        else:
            # This is either significant or insignificant (e.g.,
            # INDETERMINATE). In this case, we continue shifting back.
            return is_preceding_significant(tokens, index - 1)

    def get_significance(self, token):
        """Gets the significance of the token."""

        if re.match(r'[\s\'"`,\.\?!]', token):
            return INSIGNIFICANT

        return SIGNIFICANT

    def tokenize(self, input_string):
        """Breaks apart the input string and returns an array of token
        characters."""

        # Start with an array of tokens.
        tokens = []

        # Go through with an index
        index = 0

        while index < len(input_string):
            [token, offset] = self.pop_token(input_string[index:])
            tokens.append(token)
            index += offset

        # Return the resulting tokens.
        return tokens

    def pop_token(self, input_string):
        """Returns the next token off the input string."""

        # Grab the character and see if we have a single special character.
        c = input_string[0]

        if c in QUOTE_CHARACTERS or c is PUNCT_CHARACTERS:
            return c, 1

        # If we have a space character, then grab those as a single token.
        match = re.match(r'^(\s+)', input_string)

        if match:
            return match.group(1), len(match.group(1))

        # 1-3 dashs are tokens.
        match = re.match(r'(-{1,3})', input_string)

        if match:
            if len(match.group(1)) == 2:
                return self.en_dash, 2
            elif len(match.group(1)) == 3:
                return self.em_dash, 3
            else:
                return match.group(1), len(match.group(1))

        # Three periods are an ellipse.
        match = re.match(r'(\.{3})', input_string)

        if match:
            return self.ellipsis, len(match.group(1))

        # Pull off a block of normal characters.
        match = re.match(r'^([^\s.,;\'"`<>]+)', input_string)

        if match:
            return match.group(1), len(match.group(1))

        # No idea, just grab the first one.
        return c, 1


class XmlTypographicalConvertor(TypographicalConvertor):
    def pop_token(self, input_string):
        """Returns the next token off the input string."""

        match = re.match(r'(<[^>]+>)', input_string)

        if match:
            return match.group(1), len(match.group(1))

        return super(XmlTypographicalConvertor, self).pop_token(
            input_string)

    def get_significance(self, token):
        """This ignores all the XML tags as indeterminated."""

        if token[0] == '<':
            return INDETERMINATE

        return super(XmlTypographicalConvertor, self).get_significance(
            token)

class DocBookTypographicalConvertor(XmlTypographicalConvertor):
    def __init__(self):
        super(DocBookTypographicalConvertor, self).__init__()

        self.use_docbook()

    def use_docbook(self):
        self.close_double_quote = "</quote>"
        self.close_ended_double_quote = "</quote>"
        self.close_ended_single_quote = "</quote>"
        self.close_ended_tick_quote = "</foreignphrase>"
        self.close_single_quote = "</quote>"
        self.close_tick_quote = "</foreignphrase>"
        self.open_double_quote = "<quote>"
        self.open_ended_double_quote = "<quote role='open'>"
        self.open_ended_single_quote = "<quote role='singleopen'>"
        self.open_ended_tick_quote = "<foreignphrase role='open'>"
        self.open_single_quote = "<quote role='single'>"
        self.open_tick_quote = "<foreignphrase>"
        self.apostrophe = "'"
        self.en_dash = CLOSE_SINGLE_QUOTE
        self.em_dash = EM_DASH
        self.ellipsis = ELLIPSIS

    def process_token(self, input_string, index):
        # Get the base implementation of the token
        token, token_type = (
            super(DocBookTypographicalConvertor, self)
            .process_token(input_string, index))

        # If this is an end paragraph, we change the token type.
        if token == "</para>" or token == "</simpara>":
            token_type = TERMINAL_TOKEN

        return token, token_type

    def get_significance(self, token):
        """This ignores all the XML tags as indeterminated."""

        if re.match('^<(para|simpara)', token):
            return INSIGNIFICANT

        return super(DocBookTypographicalConvertor, self).get_significance(
            token)
