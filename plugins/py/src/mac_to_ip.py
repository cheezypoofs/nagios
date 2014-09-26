#!/usr/bin/env python
'''
nagios plugin helper to allow mac address instead of ip for operations.

It's not really a plugin, and doesn't follow the plugin conventions, but its purpose
is to be used with plugins to allow you to set the mac address instead of IP
for systems where the IPs may be dynamic.

The way to use this is like:

define command {
    command_name    check-host-alive-mac
    command_line    /usr/lib/nagios/plugins/check_ping -H `/usr/lib/nagios/plugins/mac_to_ip $HOSTADDRESS$` -w 5000,100% -c 5000,100% -p 1
}

Of course, you could use the $_HOSTMACADDRESS$ macro and set _MACADDRESS instead of using the HOSTADDRESS variable.

The result of the command should always be 0, and the output will be one of:
<the actual ip address>
"notfound"
"faileld"

So, in the case where this lookup doesn't work, you'll get some indication in the error message
in the UI.

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''


import json
import os
import pwd
import subprocess
import sys
import tempfile
import time

class Mac(object):
    '''
    Wrapper around mac address to parse and normalize mac operations
    '''
    @staticmethod
    def normalize(addr):
        mac = addr.replace(':', '').replace('-', '').lower()
        if 12 != len(mac):
            raise ValueError("Invalid mac '%s'" % addr)

        return [
            int(mac[i:(i + 2)], 16) for i in range(0, 12, 2)
        ]

    def __init__(self, mac):
        self.__address = Mac.normalize(mac)

    def display(self, delim=':'):
        return delim.join(["%.2x" % v for v in self.__address])

    def simple(self):
        return self.display(delim='')

    def __str__(self):
        return self.display()

    def __hash__(self):
        return hash(self.display())

    def __cmp__(self, other):
        if not isinstance(other, Mac):
            return -1
        return cmp(self.display(delim=''), other.display(delim=''))

def is_IP(ip):
    '''
    Is the value an IP?

    This tests a little deeper than a regex, and allows octets like "01", which ping
    also allows so I'm ok with it
    '''
    octets = ip.split('.')
    if len(octets) != 4:
        return False
    try:
        for o in [int(o) for o in octets]:
            if o < 0 or o > 255:
                return False
    except ValueError:
        return False
    return True

class MacLookupCache(object):
    '''
    Keep the results of the last call in a file for easy access.

    The caller can specify a freshness value to force a refresh.

    This class uses arp-scan to populate a mac->ip lookup and stores the data in
    a json format
    '''

    def __init__(self, fname):
        self.__fname = fname
        self.__cached = None

    def mtime(self):
        try:
            return os.stat(self.__fname).st_mtime
        except OSError:
            return 0

    def write(self, obj):
        with open(self.__fname, 'w') as f:
            f.write(json.dumps(obj))

    def read(self):
        try:
            with open(self.__fname, 'r') as f:
                return json.loads(f.read())
        except OSError:
            return None

    def lookup(self, mac, freshness=30):
        assert isinstance(mac, Mac)

        if (self.mtime() + freshness) <= time.time():
            print >> sys.stderr, "We need a fresh reading"
            # Go get a fresh reading if we're due
            self.__cached = self.__fetch()
        else:
            if self.__cached is None:
                # Read the cached result (if exists)
                self.__cached = self.read()

            if (self.__cached is None) or not self.__cached.has_key(mac.simple()):
                # If we didn't have one, or the value requested isn't there, get a fresh
                # reading.
                self.__cached = self.__fetch()

        assert self.__cached is not None, "cache should be set by all paths"
        return self.__cached[mac.simple()]

    @staticmethod
    def parse(data):
        '''
        Parse the arp-scan output and return a dict of mac: ip 's
        '''
        result = {}
        for line in data.split('\n'):
            tokens = line.split()
            if len(tokens) < 3 or not is_IP(tokens[0]):
                continue
            mac = Mac(tokens[1])
            result[mac.simple()] = tokens[0]
        return result

    def __fetch(self):

        p = subprocess.Popen(['/usr/bin/sudo', '-n', '/usr/bin/arp-scan', '-l'], stdout=subprocess.PIPE)
        p.wait()
        if p.returncode:
            raise Exception("Unexpected value running arp-scan. Is it installed and can this user sudo?")

        result = self.parse(p.stdout.read())
        self.write(result)
        return result

if __name__ == "__main__":
    try:
        to_find = sys.argv[1]
        mac = Mac(to_find)

        cache_file = os.path.join('/tmp', "." + pwd.getpwuid(os.getuid()).pw_name + ".mac_to_ip.cache")
        cache = MacLookupCache(cache_file)
        print cache.lookup(mac, freshness=300) # Allow up to 5 minutes
    except KeyError:
        print "notfound"
    except Exception, e:
        print >> sys.stderr, "Failure: %s" % str(e)
        print "failed"
