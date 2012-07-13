#!/usr/bin/python

#
# Imports
#

# System Imports
import hashlib
import imp
import os
import sys
import unittest

local_directory = os.path.normpath(os.path.dirname(__file__))
src_directory = os.path.realpath(local_directory + "/../src")

sys.path.insert(0, src_directory)

import mfgames_writing.type

#
# Unit Test
#

class TypeTests(unittest.TestCase):
    def run_test(self, tqc, input_string, expected_string):
        # Set up the default type.
        tqc.open_double_quote = "_OD_"
        tqc.close_double_quote = "_CD_"
        tqc.open_ended_double_quote = "_OED_"
        tqc.close_ended_double_quote = "_CED_"
        tqc.open_ended_single_quote = "_OES_"
        tqc.close_ended_single_quote = "_CES_"
        tqc.open_ended_tick_quote = "_OET_"
        tqc.close_ended_tick_quote = "_CET_"
        tqc.open_single_quote = "_OS_"
        tqc.close_single_quote = "_CS_"
        tqc.open_tick_quote = "_OT_"
        tqc.close_tick_quote = "_CT_"
        tqc.apostrophe = "_A_"
        tqc.en_dash = "_EN_"
        tqc.em_dash = "_EM_"
        tqc.ellipsis = "_E_"

        # Action
        output_string = tqc.convert(input_string)
        
        # Assert
        self.assertEqual(
            expected_string,
            output_string,
            "Unexpected results: " + os.linesep +
            "   Input: " + input_string + os.linesep +
            "Expected: " + expected_string + os.linesep +
            "  Output: " + output_string)

    def run_default(self, input_string, expected_string):
        tqc = mfgames_writing.type.TypographicalConvertor()
        self.run_test(tqc, input_string, expected_string)

    def run_xml(self, input_string, expected_string):
        tqc = mfgames_writing.type.XmlTypographicalConvertor()
        self.run_test(tqc, input_string, expected_string)

    def run_docbook(self, input_string, expected_string):
        tqc = mfgames_writing.type.DocBookTypographicalConvertor()
        self.run_test(tqc, input_string, expected_string)

    # def test_unquoted(self):
    #     self.run_default(
    #         'One two three.',
    #         'One two three.')

    # def test_unquoted_spaces(self):
    #     self.run_default(
    #         "One\ttwo    three.",
    #         "One\ttwo    three.")

    # def test_double(self):
    #     self.run_default(
    #         'One "two" three.',
    #         'One _OD_two_CD_ three.')

    # def test_start_double(self):
    #     self.run_default(
    #         '"One two" three.',
    #         '_OD_One two_CD_ three.')

    # def test_end_double(self):
    #     self.run_default(
    #         'One "two three."',
    #         'One _OD_two three._CD_')

    # def test_end_double(self):
    #     self.run_default(
    #         'One "two three.',
    #         'One _OED_two three._CED_')

    # def test_single(self):
    #     self.run_default(
    #         "One 'two' three.",
    #         "One _OS_two_CS_ three.")

    # def test_nested_1(self):
    #     self.run_default(
    #         "One \"'two'\" three.",
    #         "One _OD__OS_two_CS__CD_ three.")

    # def test_nested_2(self):
    #     self.run_default(
    #         "One \"'\"two\"'\" three.",
    #         "One _OD__OS__OD_two_CD__CS__CD_ three.")

    # def test_start_single(self):
    #     self.run_default(
    #         "'One two' three.",
    #         "_OS_One two_CS_ three.")

    # def test_end_single(self):
    #     self.run_default(
    #         "One 'two three.'",
    #         "One _OS_two three._CS_")

    # def test_xml_double(self):
    #     self.run_xml(
    #         '<b>One "two" three.</b>',
    #         '<b>One _OD_two_CD_ three.</b>')

    # def test_double(self):
    #     self.run_xml(
    #         '<b>One <e>"two"</e> three.</b>',
    #         '<b>One <e>_OD_two_CD_</e> three.</b>')

    # def test_tick(self):
    #     self.run_default(
    #         'One `two` three.',
    #         'One _OT_two_CT_ three.')

    # def test_start_tick(self):
    #     self.run_default(
    #         '`One two` three.',
    #         '_OT_One two_CT_ three.')

    # def test_end_tick(self):
    #     self.run_default(
    #         'One `two three.`',
    #         'One _OT_two three._CT_')

    # def test_contraction(self):
    #     self.run_default(
    #         "One it's two.",
    #         "One it_A_s two.")

    # def test_ending_contraction(self):
    #     self.run_default(
    #         "One boss' two.",
    #         "One boss_A_ two.")

    # def test_dash(self):
    #     self.run_default(
    #         "One - two.",
    #         "One - two.")

    # def test_endash(self):
    #     self.run_default(
    #         "One -- two.",
    #         "One _EN_ two.")

    # def test_emdash(self):
    #     self.run_default(
    #         "One --- two.",
    #         "One _EM_ two.")

    # def test_ellipsis(self):
    #     self.run_default(
    #         "One ... two.",
    #         "One _E_ two.")

    # def test_ellipsis_period(self):
    #     self.run_default(
    #         "One .... two.",
    #         "One _E_. two.")

    # def test_docbook_para(self):
    #     self.run_docbook(
    #         '<para>One two three.</para>',
    #         '<para>One two three.</para>')

    # def test_docbook_quotes(self):
    #     self.run_docbook(
    #         '<para>One "two" three.</para>',
    #         '<para>One _OD_two_CD_ three.</para>')

    # def test_docbook_ended_paragraphs(self):
    #     self.run_docbook(
    #         '<para>"I said</para><para>"You like cheese."</para>',
    #         "<para>_OED_I said_CED_</para><para>_OD_You like cheese._CD_</para>")

    def test_docbook_tis(self):
        self.run_docbook(
            '<para>"\'eh, boss?"</para>',
            '<para>_OD_\'eh, boss?_CD_</para>')

#
# Entry
#

if __name__ == '__main__':
    unittest.main()
