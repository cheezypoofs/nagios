#!/usr/bin/env python2.7
'''
Test the check_critical plugin (helper)

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import os
import subprocess
import unittest

class TestCheckCritical(unittest.TestCase):
    '''
    Test the trivial function of check_critical script
    '''

    CMD = '''python -c 'import sys;sys.stderr.write("STDERR");sys.stdout.write("STDOUT");sys.exit(int(sys.argv[1]));' %(rc)d'''
    CHECK_CRITICAL_CMD = os.path.join(os.path.dirname(__file__), os.pardir, 'src', 'check_critical')

    def __runCmd(self, rc):
        cmdl = [self.CHECK_CRITICAL_CMD, '/bin/bash', '-c', self.CMD % {'rc': rc}]
        p = subprocess.Popen(cmdl, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        self.assertEquals(p.stdout.read(), "STDOUT")
        self.assertEquals(p.stderr.read(), "STDERR")
        return p.returncode

    def testMe(self):
        '''
        All the script does is map return codes and return same output. That's
        easy to mimic
        '''
        self.assertEquals(2, self.__runCmd(0))
        self.assertEquals(1, self.__runCmd(1))
        self.assertEquals(0, self.__runCmd(2))
        self.assertEquals(3, self.__runCmd(3))


if __name__ == "__main__":
    unittest.main()
