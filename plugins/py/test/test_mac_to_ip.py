#!/usr/bin/env python2.7
'''
Test the mac_to_ip plugin helper

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import os
import subprocess
import tempfile
import unittest

import mac_to_ip

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

class TestMac(unittest.TestCase):
    def testNormalize(self):
        goods = [
            ('01236789abCD', [0x01, 0x23, 0x67, 0x89, 0xab, 0xcd]),
        ]
        bads = [
            '0123456',
            'abcdefghijkl'
        ]

        for test, expected in goods:
            self.assertEquals(expected, mac_to_ip.Mac.normalize(test))

        for bad in bads:
            print "Testing %(mac)s" % {'mac': bad}
            with self.assertRaises(ValueError):
                mac_to_ip.Mac(bad)

    def testDisplay(self):
        self.assertEquals('00:11:22:33:44:55', mac_to_ip.Mac('001122334455').display())
        self.assertEquals('aabbccddeeff', mac_to_ip.Mac('AABBCCDDEEFF').display(delim=''))

    def testCompare(self):
        self.assertEquals(mac_to_ip.Mac('001122334455'), mac_to_ip.Mac('001122334455'))
        self.assertNotEquals(mac_to_ip.Mac('aa1122334455'), mac_to_ip.Mac('001122334455'))

class TestIsIp(unittest.TestCase):

    def testMe(self):
        self.assertTrue(mac_to_ip.is_IP('0.0.0.0'))
        self.assertTrue(mac_to_ip.is_IP('255.255.255.255'))
        self.assertTrue(mac_to_ip.is_IP('0.02.3.004'))

        self.assertFalse(mac_to_ip.is_IP('1.1.1.'))
        self.assertFalse(mac_to_ip.is_IP('1.1.1.256'))
        self.assertFalse(mac_to_ip.is_IP('256.1.1.0'))
        self.assertFalse(mac_to_ip.is_IP('.1.1.0'))

class TestCache(unittest.TestCase):

    def setUp(self):
        self.__tmp_file = tempfile.NamedTemporaryFile()
        with open(self.__tmp_file.name, 'w') as f:
            f.write('''{
                "001122334455": "1.1.1.1",
                "aabbccddeeff": "1.1.1.2"
            }''')

    def testBasics(self):
        cache = mac_to_ip.MacLookupCache(self.__tmp_file.name)
        cache.write({
            'one': 1,
         })
        self.assertEquals(cache.read()['one'], 1)

        self.assertFalse(not cache.mtime())

    def testParsing(self):
        data = '''Interface: eth0, datalink type: EN10MB (Ethernet)
Starting arp-scan 1.8.1 with 256 hosts (http://www.nta-monitor.com/tools/arp-scan/)
192.168.25.1    0c:60:76:02:b8:3a    Hon Hai Precision Ind. Co.,Ltd.
192.168.25.3    00:1e:e5:a3:1d:b3    Cisco-Linksys, LLC
192.168.25.4    14:35:8b:11:b5:ac    (Unknown)
192.168.25.10    08:00:27:ea:40:69    CADMUS COMPUTER SYSTEMS
192.168.25.15    bc:30:5b:e1:ab:f1    Dell Inc.
192.168.25.16    00:1c:c4:88:2c:89    Hewlett Packard
192.168.25.30    08:00:27:c1:ea:c9    CADMUS COMPUTER SYSTEMS
192.168.25.32    00:1c:c4:4c:12:4b    Hewlett Packard
192.168.25.17    00:23:6c:9b:15:f4    Apple, Inc
192.168.25.80    00:0c:29:04:e6:19    VMware, Inc.
192.168.25.13    90:18:7c:18:55:e8    (Unknown)
192.168.25.105    00:0d:4b:80:df:12    Roku, LLC
192.168.25.113    08:00:27:f6:f6:9e    CADMUS COMPUTER SYSTEMS
192.168.25.118    00:17:f2:c4:6b:a9    Apple Computer
192.168.25.120    00:0d:4b:80:df:12    Roku, LLC
192.168.25.104    00:23:6c:9b:15:f4    Apple, Inc
192.168.25.102    00:0d:4b:f1:da:8d    Roku, LLC
192.168.25.111    00:1e:8f:e7:43:37    CANON INC.
192.168.25.117    00:a0:96:78:4f:8a    MITUMI ELECTRIC CO., LTD.
192.168.25.119    a0:02:dc:b3:f9:e7    (Unknown)
192.168.25.230    08:00:27:30:fd:9a    CADMUS COMPUTER SYSTEMS
192.168.25.231    08:00:27:c1:24:b6    CADMUS COMPUTER SYSTEMS

23 packets received by filter, 0 packets dropped by kernel
Ending arp-scan 1.8.1: 256 hosts scanned in 1.441 seconds (177.65 hosts/sec). 22 responded
'''
        parsed = mac_to_ip.MacLookupCache.parse(data)
        self.assertEquals(parsed['a002dcb3f9e7'], '192.168.25.119')
        self.assertFalse(parsed.has_key('a002dcb3f9e6'))



if __name__ == "__main__":
    unittest.main()
