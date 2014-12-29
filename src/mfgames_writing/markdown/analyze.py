"""Code to analyze a Markdown file and produce various information and analysis about the contents."""


import nltk
import nltk.stem.lancaster
import nltk.tokenize.punkt
import nltk.data
import codecs
import logging
import mfgames_tools.process
import mfgames_writing
import os
import shutil
import sys
import yaml


class MarkdownAnalyzeProcess(mfgames_tools.process.InputFileProcess):
    """Primary process for analyzing a Markdown file and giving
    information and warnings about it."""

    def __init__(self):
        super(MarkdownAnalyzeProcess, self).__init__()
        self.log = logging.getLogger("analyze")
        self.meta = None
        self.paras = []
        self.sents = []
        self.tokens = []
        self.statuses = []
        self.min_score = 50

        # Set up the NLTK elements.
        self.stemmer = nltk.stem.lancaster.LancasterStemmer()
        self.sent_tokenizer = nltk.tokenize.punkt.PunktSentenceTokenizer()

    def setup_arguments(self, parser):
        """Sets up the command-line arguments for processing."""

        # Add in the argument from the base class.
        super(MarkdownAnalyzeProcess, self).setup_arguments(parser)

        parser.add_argument(
            '--minimum-score', '-m',
            type=int,
            default=100,
            help="The minimum score to showx")

    def get_help(self):
        return "Merges a DocBook file and all includes and gathers up external resources such as images."

    def process(self, args):
        # Set up the internal variables.
        self.min_score = args.minimum_score

        # Handle the base class' processing which verifies the file
        # already exists.
        super(MarkdownAnalyzeProcess, self).process(args)

    def process_file(self, filename):
        # Start by reading in the file and populating the internal
        # list of paragraphs and metadata.
        self.log.debug(filename)
        self.read_file(filename)

        # Perform the analysis on the document.
        EchoWordsPlugin(self).analyze()
        SentenceHeadStructurePlugin(self).analyze()
        SentenceHeadWordPlugin(self).analyze()

        # Write the output.
        PrintAnalyzeOutput().output(self)

    def read_file(self, path):
        with open(path, 'rb') as fd:
            # Grab the first line, that will determine if we are
            # reading in YAML metadata or just going straight to the
            # lines.
            line = fd.readline()
            line_index = 1

            if line.startswith('---'):
                # This is a YAML metadata, so pull it all together
                # until we get ot the next --- which indicates the
                # end.
                metadata_lines = [line]

                while line:
                    # Save this line momentarily.
                    next_line = line

                    # Read the next line.
                    line = fd.readline()
                    line_index += 1

                    if next_line.startswith("---"):
                        # Grab the next line to avoid passing the ---
                        # to the next step.
                        line = fd.readline()
                        line_index += 1

                        # Parse the YAML so we have access to it.
                        self.meta = yaml.load("\n".join(metadata_lines))
                        break

                    metadata_lines.append(next_line)

            # Otherwise, slurp in the rest of the file and parse them
            # into paragraphs. We skip blank lines because they aren't
            # really important except for grouping lines
            # together. Unfortunately, we don't really have a good
            # Markdown parser that does this for us.
            lines = []

            while line:
                # If the line is a blank line, then we need to finish
                # up the previous paragraph.
                if len(line.strip()) == 0:
                    # We have a blank line. So check to see if we have
                    # any gathered lines for combining into a single
                    # one.
                    if len(lines) > 0:
                        # Combine the lines together and create a
                        # paragraph out of them.
                        combined = " ".join(lines).strip()

                        # We skip some certain lines.
                        if combined.startswith("---"):
                            pass
                        elif combined.startswith("#"):
                            pass
                        elif combined.startswith("LocalWords:"):
                            pass
                        else:
                            para = Paragraph(
                                self,
                                line_index - len(lines) - 1,
                                len(self.paras),
                                combined)
                            self.paras.append(para)

                        # Clear out the line buffer for the next one.
                        lines = []

                    # Grab the next line and continue.
                    line = fd.readline()
                    line_index += 1
                    continue

                lines.append(line)

                # Read in the next line and stop if we run out.
                line = fd.readline();
                line_index += 1

            if len(lines) > 0:
                # Combine the lines together and create a
                # paragraph out of them.
                combined = " ".join(lines).strip()

                # We skip some certain lines.
                if combined.startswith("---"):
                    pass
                elif combined.startswith("#"):
                    pass
                elif combined.startswith("LocalWords:"):
                    pass
                else:
                    para = Paragraph(
                        self,
                        line_index - len(lines) - 1,
                        len(self.paras),
                        combined)
                    self.paras.append(para)

            self.log.debug(
                "Found " + format(len(self.paras)) + " paragraphs")
            self.log.debug(
                "Found " + format(len(self.sents)) + " sentences")
            self.log.debug(
                "Found " + format(len(self.tokens)) + " tokens")

    def get_nearest_words(self, tokenref, scalar):
        """
        Retrieves the surrounding tokens in a tuple of two lists, the first being elements before this token and the second being units before and after.
        """

        # Start by creating our two lists.
        before = []
        after = []

        # With token searching, we just get the index and move back.
        token_index = tokenref.token_index
        start_index = max(0, token_index - scalar)
        end_index = min(len(self.tokens), token_index + scalar)

        # Start by going through the elements before this one.
        for index in range(start_index, token_index):
            before.append(self.tokens[index])

        for index in range(token_index + 1, end_index):
            after.append(self.tokens[index])

        # Return the resulting tuple.
        return [before, after]

    def get_nearest_sents(self, sent, scalar):
        # Start by creating our two lists.
        before = []
        after = []

        # With sentence searching, we just get the index and move back.
        sent_index = sent.sent_index
        start_index = max(0, sent_index - scalar)
        end_index = min(len(self.sents), sent_index + scalar)

        # Start by going through the elements before this one.
        for index in range(start_index, sent_index):
            before.append(self.sents[index])

        for index in range(sent_index + 1, end_index):
            after.append(self.sents[index])

        # Return the resulting tuple.
        return [before, after]


class Paragraph:
    def __init__(self, process, line_index, para_index, text):
        # Save the member variables. We also strip off some of the
        # Markdown formatting from the text because it isn't important
        # for analyzing.
        self.process = process
        self.line_index = line_index
        self.para_index = para_index
        self.text = text.replace("*", "")
        self.sents = []

        # Break apart the sentences and add them to the list.
        sent_texts = process.sent_tokenizer.sentences_from_text(self.text, True)

        for sent_text in sent_texts:
            sent = Sentence(self, len(self.process.sents), sent_text)
            self.sents.append(sent)
            self.process.sents.append(sent)


class Sentence:
    def __init__(self, para, sent_index, text):
        # Save the simple member variables.
        self.para = para
        self.process = para.process
        self.sent_index = sent_index
        self.text = text
        self.tokens = []
        
        # Split apart the words into tokens and then do a
        # parts-of-speech analysis on them.
        tokens = nltk.word_tokenize(text)
        tagged = nltk.pos_tag(tokens)

        for tag in tagged:
            token = Token(self, len(self.process.tokens), tag)
            self.tokens.append(token)
            self.process.tokens.append(token)


class Token:
    def __init__(self, sent, token_index, nltk_token):
        self.sent = sent
        self.para = sent.para
        self.process = sent.para.process
        self.text = nltk_token[0]
        self.pos = nltk_token[1]
        self.token_index = token_index
        self.stem = self.process.stemmer.stem(self.text)


class PrintAnalyzeOutput:
    def output(self, process):
        min_score = process.min_score
        s = filter(lambda s: s.before_score >= min_score, process.statuses)
        s = sorted(s, key=lambda s: s.before_score)

        for status in s:
            self.write(status)

    def write(self, status):
        score = "- {0:5} {1}".format(
            status.before_score,
            status.label)

        if status.token:
            print "{0:4} {1:20} ({2:3} {3:10} {5}) {4}".format(
                status.token.para.line_index,
                status.token.text,
                status.token.pos,
                status.token.stem,
                score,
                len(status.before_tokens))

        if status.sent:
            print "{0:4} {1:39} {4}".format(
                status.sent.para.line_index,
                status.sent.text[0:39],
                "",
                "",
                score,
                len(status.before_sents))


class AnalyzeStatus:
    def __init__(self, label):
        self.label = label
        self.before_score = 0
        self.after_score = 0
        self.combined_score = 0
        self.token = None
        self.before_token = None
        self.after_token = None
        self.sent = None
        self.before_sents = None
        self.after_sents = None

    def has_score(self):
        if self.before_score > 0:
            return True
        if self.after_score > 0:
            return True
        if self.combined_score > 0:
            return True
        return False

    def set_score(self, score):
        if self.token:
            self.before_score = self.get_token_score(score, self.before_tokens)
            self.after_score = self.get_token_score(score, self.after_tokens)
            self.combined_score = self.get_token_score(
                score, self.before_tokens + self.after_tokens)

        if self.sent:
            self.before_score = self.get_sent_score(score, self.before_sents)
            self.after_score = self.get_sent_score(score, self.after_sents)
            self.combined_score = self.get_sent_score(
                score, self.before_sents + self.after_sents)

    def get_token_score(self, score, tokens):
        # Start by calculating the score based on the totals.
        current_score = len(tokens) * score.count_score

        # On top of this, we add a score for the inverse distance from
        # the current token to the current one.
        max_distance_score = score.scalar * score.token_distance_score

        for token in tokens:
            distance = abs(self.token.token_index - token.token_index)
            distance_score = distance * score.token_distance_score
            token_score = max_distance_score - distance_score
            current_score += token_score

        # Return the resulting score.
        return current_score

    def get_sent_score(self, score, sents):
        # Start by calculating the score based on the totals.
        current_score = len(sents) * score.count_score

        # On top of this, we add a score for the inverse distance from
        # the current sent to the current one.
        max_distance_score = score.scalar * score.sent_distance_score

        for sent in sents:
            distance = abs(self.sent.sent_index - sent.sent_index)
            distance_score = distance * score.sent_distance_score
            sent_score = max_distance_score - distance_score
            current_score += sent_score

        # Return the resulting score.
        return current_score


class AnalyzeScore:
    def __init__(
            self,
            count_score,
            token_distance_score = 0,
            scalar = 50,
            scope = 'words'):
        self.count_score = count_score
        self.scalar = scalar
        self.scope = scope
        self.token_distance_score = token_distance_score
        self.sent_distance_score = 0


class AnalyzePlugin:
    def __init__(self):
        self.score = AnalyzeScore(50)
        self.scores = {}


class EchoWordsPlugin(AnalyzePlugin):
    def __init__(self, process):
        AnalyzePlugin.__init__(self)
        self.process = process
        self.log = process.log

        self.score = AnalyzeScore(50, 10)
        self.scores['PRP'] = AnalyzeScore(5, 1)
        self.scores['DT'] = AnalyzeScore(5, 1)
        self.scores['NNP'] = AnalyzeScore(0)
        self.scores['NN'] = AnalyzeScore(0)
        self.scores['CD'] = AnalyzeScore(0)
        self.scores['VBD'] = AnalyzeScore(10, 5)
        self.scores['POS'] = AnalyzeScore(0)
        self.scores['VBZ'] = AnalyzeScore(5, 5)
        self.scores['RB'] = AnalyzeScore(10, 5)
        self.scores['IN'] = AnalyzeScore(10, 5)
        self.scores['TO'] = AnalyzeScore(5, 1)
        self.scores['CC'] = AnalyzeScore(10, 5)
        self.scores[':'] = AnalyzeScore(0)
        self.scores['.'] = AnalyzeScore(0)
        self.scores[','] = AnalyzeScore(0)
        self.scores['PRP$'] = AnalyzeScore(5, 1)

    def analyze(self):
        # Loop through all the tokens in the list and look for
        # repeated words.
        for token in self.process.tokens:
            # Figure out which score we're using. This also determines
            # how far we are looking for a given phrase and its scope.
            score = self.score

            if token.pos in self.scores:
                score = self.scores[token.pos]

            # Retrieve the surrounding words
            surrounding = self.process.get_nearest_words(
                token,
                score.scalar)

            # Figure out all the tokens that match the current
            # one. This is what drives the scoring and calculations.
            before_tokens = []
            after_tokens = []
            
            for before in surrounding[0]:
                if before.stem == token.stem:
                    before_tokens.append(before)
            
            for after in surrounding[1]:
                if after.stem == token.stem:
                    after_tokens.append(after)

            # If we don't have a count, then don't bother doing
            # anything else.
            after_count = len(after_tokens)
            before_count = len(before_tokens)

            if after_count + before_count == 0:
                continue

            # Calculate the score based on the counts.
            status = AnalyzeStatus("Echoed stem words")
            status.token = token
            status.before_tokens = before_tokens
            status.after_tokens = after_tokens
            status.set_score(score)

            # Only include them if we have a score.
            if status.has_score():
                self.process.statuses.append(status)


class SentenceHeadStructurePlugin(AnalyzePlugin):
    def __init__(self, process):
        AnalyzePlugin.__init__(self)
        self.process = process
        self.log = process.log
        self.score = AnalyzeScore(200, 0, 5, 'sentences')
        self.score.sent_distance_score = 200

    def analyze(self):
        # Loop through all of the sentences and look for similiar structures.
        for sent in self.process.sents:
            # Figure out which score we're using. This also determines
            # how far we are looking for a given phrase and its scope.
            score = self.score

            # Get the surrounding sentences.
            surrounding = self.process.get_nearest_sents(
                sent,
                score.scalar)

            # Figure out all the sents that match the current
            # one. This is what drives the scoring and calculations.
            sent_struct = self.get_struct(sent)
            before_sents = []
            after_sents = []
            
            for before in surrounding[0]:
                if self.get_struct(before) == sent_struct:
                    before_sents.append(before)
            
            for after in surrounding[1]:
                if self.get_struct(after) == sent_struct:
                    after_sents.append(after)

            # If we don't have a count, then don't bother doing
            # anything else.
            after_count = len(after_sents)
            before_count = len(before_sents)

            if after_count + before_count == 0:
                continue

            # Calculate the score based on the counts.
            status = AnalyzeStatus("Sentence head structure")
            status.sent = sent
            status.before_sents = before_sents
            status.after_sents = after_sents
            status.set_score(score)

            # Only include them if we have a score.
            if status.has_score():
                self.process.statuses.append(status)

    def get_struct(self, sent):
        tokens = sent.tokens[0:3]
        structs = []

        for token in tokens:
            structs.append(token.pos)

        return " ".join(structs)


class SentenceHeadWordPlugin(AnalyzePlugin):
    def __init__(self, process):
        AnalyzePlugin.__init__(self)
        self.process = process
        self.log = process.log
        self.score = AnalyzeScore(100, 0, 5, 'sentences')
        self.score.sent_distance_score = 100

    def analyze(self):
        # Loop through all of the sentences and look for similiar structures.
        for sent in self.process.sents:
            # Figure out which score we're using. This also determines
            # how far we are looking for a given phrase and its scope.
            score = self.score

            # Get the surrounding sentences.
            surrounding = self.process.get_nearest_sents(
                sent,
                score.scalar)

            # Figure out all the sents that match the current
            # one. This is what drives the scoring and calculations.
            sent_token = self.get_token(sent)
            before_sents = []
            after_sents = []
            
            for before in surrounding[0]:
                if self.get_token(before) == sent_token:
                    before_sents.append(before)
            
            for after in surrounding[1]:
                if self.get_token(after) == sent_token:
                    after_sents.append(after)

            # If we don't have a count, then don't bother doing
            # anything else.
            after_count = len(after_sents)
            before_count = len(before_sents)

            if after_count + before_count == 0:
                continue

            # Calculate the score based on the counts.
            status = AnalyzeStatus("Sentence head token")
            status.sent = sent
            status.before_sents = before_sents
            status.after_sents = after_sents
            status.set_score(score)

            # Only include them if we have a score.
            if status.has_score():
                self.process.statuses.append(status)

    def get_token(self, sent):
        index = 0
        while True:
            stem = sent.tokens[index].stem
            index += 1

            if stem == '"':
                pass
            else:
                return stem

            
