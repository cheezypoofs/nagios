#!/usr/bin/env python
'''
This is a pretty useless nagios plugin to actually install.

This is a sample useful for showing how to use the nagios module
to implement a plugin implementation.

The --warning and --critical parameters are used in conjunction with
a --min/-n --max/-x pair to generate a random integer and create a
report accordingly.

Obviously, if you run this in your environment, you will see failures! :)

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import random
import sys

import nagios.plugins as plugins

class CheckRandom(plugins.PluginBase):
    '''
    "checks" a random number between --min and --max. --warning and --critical are
    issued according to those thresholds.
    '''

    VERSION = "1.0"
    DEFAULT_WARNING = "0:90"    # Allow values between 0 and 90
    DEFAULT_CRITICAL = "0:95"   # Allow vaules between 0 and 95
    
    def __init__(self):
        super(CheckRandom, self).__init__()

        # This is how additional arguments happen
        self._parser.add_option(
            '-n', '--min', type="int", default=0, dest="min", help="Minimum random integer")
        self._parser.add_option(
            '-x', '--max', type="int", default=100, dest="max", help="Maximum random integer")

    def _run(self, opts):
        value = random.randint(opts.min, opts.max)
        msg = "value is %(value)s" % {'value': value}

        if not self._critical.is_allowed(value):
            # could also use set_simple_result with RESULT_WARNING
            raise plugins.NagiosCritical(msg)
        if not self._warning.is_allowed(value):
            # could also use set_simple_result with RESULT_CRITICAL
            raise plugins.NagiosWarning(msg)
        
        self._output.set_simple_result(msg)
    
if __name__ == "__main__":
    plugin = CheckRandom()
    plugin(sys.argv)
    assert False, "unreachable. plugin should always exit"