#!/usr/bin/env python
'''
Runs the command line given as the arguments to this script and modifies the return code.

The purpose is to run an existing plugin and translate CRITICAL (2) to SUCCESS (0) and vice
versa. One example use case is to consider a 100% ping failure a success (check for unreachable)
while 100% returns would be CRITICAL. A 50% ping return should remain as-is

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import subprocess
import sys

p = subprocess.Popen(sys.argv[1:])
p.wait()

if p.returncode == 0:
    sys.exit(2)
elif p.returncode == 2:
    sys.exit(0)
else:
    sys.exit(p.returncode)

