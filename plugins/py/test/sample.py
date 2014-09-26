#!/usr/bin/env python2.7
'''
Implement a trivial plugin using the plugins' nagios module


Good to test and also to show how to use it. A lot of the coverage here is
redundant with the unit tests, but this is a more high-level full-function
set of tests, and it shows a lot of typical use cases.

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import StringIO
import sys
import unittest

import nagios.plugins as plugins

class MyPlugin(plugins.PluginBase):
    VERSION = "0.99"
    DEFAULT_WARNING = "0:10" # 0-10 allowed
    DEFAULT_CRITICAL = ":20" # 0-20 allowed

    def __init__(self, value=None):
        self.output = StringIO.StringIO()
        super(MyPlugin, self).__init__(self.output)
        self._parser.add_option('-x', dest="testname", type="string")
        self._value = value

    def _run(self, opts):
        if not opts.testname:
            raise Exception("testname not set")
        func = getattr(self, opts.testname)
        if not func:
            raise Exception("test name %(name)s not found" % {'name': opts.testname})
        func(opts)

    def do_normal(self, opts):
        self._output.set_simple_result('passed')

    def do_normal_verbose(self, opts):
        self._output.set_simple_result('passed', "I really did pass")

    def do_normal_multiline(self, opts):
        self._output.set_simple_result('passed')
        self._output.add_multiline('Here is line one')
        self._output.add_multiline('Here is line two')

    def do_simple_warning(self, opts):
        raise plugins.NagiosWarning("oy!")

    def do_simple_critical(self, opts):
        raise plugins.NagiosCritical("oy!")

    def do_check(self, opts):
        assert self._value is not None, "Set value for this test"
        if not self._critical.is_allowed(self._value):
            raise plugins.NagiosCritical()
        if not self._warning.is_allowed(self._value):
            raise plugins.NagiosWarning()

        self._output.set_simple_result("All good")

class PluginTests(unittest.TestCase):

    def test_not_implemented(self):
        '''
        Does this blow things up, or is it handled as a "normal" exception?
        '''

        output = StringIO.StringIO()
        plugin = plugins.PluginBase(output)
        with self.assertRaises(SystemExit) as e:
            plugin([])
            self.assertEquals(plugins.RESULT_UNKNOWN, e.exception.code)
            self.assertTrue("NotImplemented" in output.getvalue())

    def test_version(self):
        plugin = MyPlugin()

        with self.assertRaises(SystemExit) as e:
            plugin(['--version'])

        self.assertEquals(plugins.RESULT_UNKNOWN, e.exception.code)
        self.assertTrue(plugin.VERSION in plugin.output.getvalue())

    def test_normal(self):
        plugin = MyPlugin()

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_normal'])

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertEquals('passed\n', plugin.output.getvalue())

    def test_normal_verbose(self):
        plugin = MyPlugin()

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_normal_verbose', '-v'])

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertEquals('I really did pass\n', plugin.output.getvalue())

    def test_normal_multiline(self):
        plugin = MyPlugin()

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_normal_multiline', '-v', '-v'])

        self.assertEquals(plugins.RESULT_OK, e.exception.code)
        self.assertTrue('line two' in plugin.output.getvalue())

    def test_simple_warning(self):
        plugin = MyPlugin()

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_simple_warning'])

        self.assertEquals(plugins.RESULT_WARNING, e.exception.code)

    def test_simple_critical(self):
        plugin = MyPlugin()

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_simple_critical'])

        self.assertEquals(plugins.RESULT_CRITICAL, e.exception.code)

    def test_configured_warning(self):
        plugin = MyPlugin(10)

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_check'])

        # Should pass until we configure 10 to be bad
        self.assertEquals(plugins.RESULT_OK, e.exception.code,
            plugin.output.getvalue())

        plugin = MyPlugin(10)
        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_check', '-w', '0:5'])

        self.assertEquals(plugins.RESULT_WARNING, e.exception.code,
            plugin.output.getvalue())

    def test_configured_critical(self):
        plugin = MyPlugin(10)

        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_check'])

        # Should pass until we configure 10 to be bad
        self.assertEquals(plugins.RESULT_OK, e.exception.code,
            plugin.output.getvalue())

        plugin = MyPlugin(10)
        with self.assertRaises(SystemExit) as e:
            plugin(['-x', 'do_check', '-w', '0:5', '-c', '0:8'])

        self.assertEquals(plugins.RESULT_CRITICAL, e.exception.code,
            plugin.output.getvalue())

if __name__ == "__main__":
    unittest.main()
