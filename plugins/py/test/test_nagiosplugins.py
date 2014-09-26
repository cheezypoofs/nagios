#!/usr/bin/env python2.7
'''
Test the nagios.plugins module

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import optparse
import os
import unittest
import StringIO

import mac_to_ip
import nagios.plugins as plugins

class OptionTests(unittest.TestCase):
    def setUp(self):
        self.__file = StringIO.StringIO()
        self.__parser = plugins.get_option_parser(version="1.0", out_file=self.__file)

    def testVerbosity(self):
        opts = plugins.parse_options(self.__parser, ['-v'])
        self.assertEquals(1, opts.verbosity)

        opts = plugins.parse_options(self.__parser, ['-v', '-v'])
        self.assertEquals(2, opts.verbosity)

        handler = plugins.OutputHandler()

        opts = plugins.parse_options(self.__parser, ['-v', '-v', '-v'], handler)
        self.assertEquals(3, opts.verbosity)

        with self.assertRaises(SystemExit):
            plugins.parse_options(self.__parser, ['-v', '-v', '-v', '-v'])

    def testHelp(self):
        with self.assertRaises(SystemExit) as e:
            plugins.parse_options(self.__parser, ['--help'])
        self.assertEquals(plugins.RESULT_UNKNOWN, e.exception.code)

    def testVersion(self):
        with self.assertRaises(SystemExit) as e:
            plugins.parse_options(self.__parser, ['-V'])
        self.assertEquals(plugins.RESULT_UNKNOWN, e.exception.code)
        self.assertTrue('1.0' in self.__file.getvalue())

        with self.assertRaises(SystemExit) as e:
            plugins.parse_options(self.__parser, ['--version'])
        self.assertEquals(plugins.RESULT_UNKNOWN, e.exception.code)
        self.assertTrue('1.0' in self.__file.getvalue())

class OutputTests(unittest.TestCase):

    def setUp(self):
        self.__file = StringIO.StringIO()
        self.__handler = plugins.OutputHandler(self.__file)
        self.__parser = plugins.get_option_parser(out_file=self.__file)

    def testSimple(self):
        plugins.parse_options(self.__parser, [], self.__handler)

        self.__handler.set_simple_result('short')
        with self.assertRaises(SystemExit) as e:
            self.__handler.display_and_exit()

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertEquals('short\n', self.__file.getvalue())

    def testSimpleIgnoreLong(self):
        '''
        With no verbosity, the result should be the short result
        '''
        plugins.parse_options(self.__parser, [], self.__handler)

        self.__handler.set_simple_result('short', 'long')
        with self.assertRaises(SystemExit) as e:
            self.__handler.display_and_exit()

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertEquals('short\n', self.__file.getvalue())

    def testSimpleLong(self):
        '''
        With verbosity >= 1, the long result should be given
        '''
        plugins.parse_options(self.__parser, ['-v'], self.__handler)

        self.__handler.set_simple_result('short', 'long')
        with self.assertRaises(SystemExit) as e:
            self.__handler.display_and_exit()

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertEquals('long\n', self.__file.getvalue())

    def testShortGivenAsLong(self):
        '''
        With verbosity >= 1, the long result should be given (but default back to short)
        '''
        plugins.parse_options(self.__parser, ['-v'], self.__handler)

        self.__handler.set_simple_result('short')
        with self.assertRaises(SystemExit) as e:
            self.__handler.display_and_exit()

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertEquals('short\n', self.__file.getvalue())

class RangeTests(unittest.TestCase):

    def test_simple(self):
        ranges = plugins.RangeThreshold._parse_range("10")
        self.assertEquals([(0, 10)], ranges)
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 0))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 10))
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, -1))
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 11))

    def test_to_infinity(self):
        ranges = plugins.RangeThreshold._parse_range("10:")
        self.assertEquals([(10, None)], ranges)
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 0))
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 9))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 10))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 11))

    def test_neg_infinity(self):
        ranges = plugins.RangeThreshold._parse_range("~:10")
        self.assertEquals([(None, 10)], ranges)
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, -1))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 10))
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 11))

    def test_infinity(self):
        # No reason not to allow ""
        ranges = plugins.RangeThreshold._parse_range("")
        self.assertEquals([(0, None)], ranges)
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, -1))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 0))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 1))

        ranges = plugins.RangeThreshold._parse_range(":")
        self.assertEquals([(0, None)], ranges)
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, -1))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 0))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 1))

    def test_start_end(self):
        ranges = plugins.RangeThreshold._parse_range("10:20")
        self.assertEquals([(10, 20)], ranges)
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 9))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 10))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 20))
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 21))

    def test_inverted_start_end(self):
        ranges = plugins.RangeThreshold._parse_range("@10:20")
        self.assertEquals([(None, 9), (21, None)], ranges)

        self.assertTrue(plugins.RangeThreshold._check_value(ranges, -1))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 0))
        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 9))

        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 10))
        self.assertFalse(plugins.RangeThreshold._check_value(ranges, 20))

        self.assertTrue(plugins.RangeThreshold._check_value(ranges, 21))

    def test_negatives(self):
        tests = [
            # non-integers
            "x",
            ":x",
            "10:x"
            "x:",
            "x:10",
            "@x",
            "~x",

            # Bad usage of @ or ~
            "@",
            "~",
            "@~0:10",
            "@10:",

            # Invalid range
            "6:5",

        ]
        for test in tests:
            with self.assertRaises(ValueError):
                plugins.RangeThreshold._parse_range(test)

    def test_optparse(self):
        '''
        Test the use case for the warning and critical thresholds.

        The caller will create  RangeThresold instance with default values
        and the optparse can then set if the -w or -c options are given.
        '''

        warning = plugins.RangeThreshold() # Default all values allowed
        critical = plugins.RangeThreshold()
        self.assertTrue(warning.is_allowed(5))
        self.assertTrue(critical.is_allowed(5))

        file_ = StringIO.StringIO()
        parser = plugins.get_option_parser(out_file=file_, warning_range=warning, critical_range=critical)

        plugins.parse_options(parser, ['-w', '10:'])
        self.assertFalse(warning.is_allowed(5))

        plugins.parse_options(parser, ['-c', '5:'])
        self.assertFalse(critical.is_allowed(4))
        self.assertTrue(critical.is_allowed(5))


if __name__ == "__main__":
    unittest.main()
