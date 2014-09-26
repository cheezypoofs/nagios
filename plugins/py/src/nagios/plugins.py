'''
Some common items and utilities to make plugins better

See: http://nagios.sourceforge.net/docs/3_0/pluginapi.html

This source is provided under the MIT License (see LICENSE.txt)
Copyright (c) 2014 Ryan C. Catherman
'''

import optparse
import sys

RESULT_OK = 0
RESULT_WARNING = 1
RESULT_CRITICAL = 2
RESULT_UNKNOWN = 3


class OutputHandler(object):
    '''
    Ensures the output conventions are used when displaying the results of the
    plugins.

    See the API doc above for more information.

    As much as possible, an instance of this class should be used in normal cases.
    In cases where RESULT_UNKNOWN is needed, this class can be bypassed.
    '''

    def __init__(self, file=sys.stdout):
        self.__simple_result = None # verbosity of 0
        self.__long_result = None # verbosity of 1 or higher
        self.__multilines = []
        self.__perf_data = []
        self.__verbosity = 0
        self.__file = file

    def file(self):
        return self.__file

    def set_verbosity(self, level):
        assert level >= 0 and level <= 3
        self.__verbosity = level

    def set_simple_result(self, result, long_result=None):
        assert self.__simple_result is None, "Simple Result should only be set once"
        self.__simple_result = result
        self.__long_result = long_result or result

    def add_multiline(self, text):
        self.__multilines.append(text)

    def add_perf_data(self):
        '''
        'label'=value[UOM];[warn];[crit];[min];[max]
        '''
        assert False, "Not implemented yet"

    def display_and_exit(self, result=RESULT_OK):
        '''
        Write the result data to stdout (default) and exit with result

        This ensures the output conventions are followed.
        '''
        assert self.__simple_result is not None, "Result was never set!"

        if 0 == self.__verbosity:
            print >> self.__file, self.__simple_result
        else:
            print >> self.__file, self.__long_result

        if 2 <= self.__verbosity:
            for line in self.__multilines:
                print >> self.__file, line

        sys.exit(result)

class _OptionParser(optparse.OptionParser):
    '''
    A subclass of OptionParser so we can special case some of the handling

    (as advised by the documentation for it)
    '''
    def __init__(self, out_file=sys.stdout, *args, **kwargs):
        optparse.OptionParser.__init__(self, *args, **kwargs)
        self.__file = out_file

    def error(self, msg):
        '''
        Display error and exit

        The convention is unclear, but the doc dictates nothing goes to stderr
        but more importantly we need to exit with UNKNOWN
        '''
        print >> self.__file, msg
        sys.exit(RESULT_UNKNOWN)

    def print_help(self, *args, **kwargs):
        '''
        Display help and exit

        The convention is unclear, but the doc dictates nothing goes to stderr
        but more importantly we need to exit with UNKNOWN
        '''
        optparse.OptionParser.print_help(self, file=self.__file)
        sys.exit(RESULT_UNKNOWN)

    def print_version(self, *args, **kwargs):
        '''
        Display version and exit

        '''
        optparse.OptionParser.print_version(self, file=self.__file)
        sys.exit(RESULT_UNKNOWN)

class RangeThreshold(object):
    def __init__(self, range_=''):
        '''
        Initialize this instance with the default range.

        The format of "range" is defined by the document:
        http://nagios-plugins.org/doc/guidelines.html
        '''
        self.set_range(range_)

    def is_allowed(self, value):
        return self._check_value(self.__ranges, value)

    def opt_parse_callback(self, option, opt_str, value, parser):
        '''
        Attempt to apply value
        '''

        try:
            self.set_range(value)
        except ValueError:
            parser.error("Invalid range option %(value)s" % {'value': value})

    def set_range(self, range_str):
        '''
        After initialization, set the range to a new value.

        Useful for just after option parsing
        '''
        self.__ranges = self._parse_range(range_str)

    @staticmethod
    def _check_value(ranges, value):
        assert type(value) in [int, long]

        # Assume False until a True is found
        for range in ranges:
            left, right = range
            if left is not None and value < left:
                continue # Can't match this range
            if right is not None and value > right:
                continue # Can't match this range
            return True

        return False

    @staticmethod
    def _parse_range(range_):
        '''
        Parse the range according to the rules defined. Return a list of tuples indicating
        the matching (allowed) ranges. If any value is None, assume infinity.

        raise ValueError if any illegal string given

        Examples of returns for each range:
        "" or ":"  --->    [(None, None)]: One range. All values match
        ":10" or "~:10" -> [(None, 10)]: One range. All values up to (and including) 10 are allowed.
        "0:"       --->    [(0, None)]: All positive values allowed
        "10:20"    --->    [(10, 20)]: 10 to 20 (inclusive) allowed
        "@10:20"   --->    [(None, 9), (21, None)]: Two ranges. Up to 9 or 21 and over allowed.

        The return value here is useful with check_value()

        From the doc...
        This is the generalised format for ranges:
        [@]start:end
        Notes:
        1. start <= end
        2. start and ":" is not required if start=0
        3. if range is of format "start:" and end is not specified, assume end is infinity
        4. to specify negative infinity, use "~"
        5. alert is raised if metric is outside start and end range (inclusive of endpoints)
        6. if range starts with "@", then alert if inside this range (inclusive of endpoints)
        '''

        # Note 6
        invert = range_ and range_[0] == '@'
        if invert:
            range_ = range_[1:]

        # Initialize to infinity on both ends
        left, right = None, None

        # Note 2
        if ':' not in range_:
            left = 0
            if range_: # else infinity
                right = int(range_)
        else:
            splits = range_.split(':', 1)


            # Note 4
            # Treat empty as 0 but ~ as negative infinity
            if not splits[0]:
                left = 0
            elif splits[0][0] != '~':
                left = int(splits[0])

            # Note 3
            # No right token
            if len(splits) == 2 and splits[1]:
                right = int(splits[1])

        # Note 1
        if left is not None and right is not None:
            if left > right:
                raise ValueError("Start cannot be larger than End")
        if invert and (left is None or right is None):
            raise ValueError("@ makes no sense without a start and end defined")


        # Now, build the return. The range returns the "matching" ranges.
        # So, in the case of "invert" (@), two ranges are returned. For example:
        # @10:20 says to alert between 10 and 20 (inclusive) instead of allow
        # this range. In this case, we return [(None, 9), (21, None)].
        if invert:
            return [(None, left - 1), (right + 1, None)]
        else:
            return [(left, right)]

def get_option_parser(
    version=None,
    out_file=sys.stdout,
    warning_range=None,
    critical_range=None,
    ):
    '''
    Create an OptionParser instance for use with your plugin.

    This initializes with all of the common plugin options (see API doc),
    as configured by the arguments.
    version: Value to display when version called.
    out_file: (default sys.stdout). Most times, you can leave this alone
    warning_range: instance of RangeThreshold or None. If specified, the -w option will
        be exposed and the RangeThreshold instance will be added to the options and configured
        accordingly.
    critical_range: instance of RangeThreshold or None
    '''

    assert warning_range is None or isinstance(warning_range, RangeThreshold)
    assert critical_range is None or isinstance(critical_range, RangeThreshold)

    if not version:
        version = "%prog (unknown version)"
    else:
        version = "%prog " + version

    parser = _OptionParser(
        out_file=out_file,
        usage="%prog [options]",
        version=version,
        add_help_option=False)

    parser.add_option("-v", "--verbose", dest="verbosity", help="Set verbosity level (up to 3)",
        action="count", default=0)
    parser.add_option("-h", "--help", help="Display usage", dest="help",
        action="store_true", default=False)

    if warning_range:
        parser.add_option(
            "-w", "--warning", dest="warning", type="string",
            help="Standard nagios warning threshold option", action="callback",
            callback=warning_range.opt_parse_callback)

    if critical_range:
        parser.add_option(
            "-c", "--critical", dest="warning", type="string",
            help="Standard nagios critical threshold option", action="callback",
            callback=critical_range.opt_parse_callback)

    # note: optparse will add --version for us
    parser.add_option("-V", help="Display version", dest="version",
        action="store_true", default=False)
    parser.set_usage("%prog [options]")

    return parser

def parse_options(parser, argv, output_handler=None):
    assert output_handler is None or isinstance(output_handler, OutputHandler)

    opts, args = parser.parse_args(argv)

    if opts.help:
        parser.print_help()

    if opts.version:
        parser.print_version()

    if opts.verbosity < 0 or opts.verbosity > 3:
        parser.error("Verbosity up to 3 allowed")
    if output_handler:
        output_handler.set_verbosity(opts.verbosity)

    return opts

class NagiosWarning(Exception):
    '''
    Implementations can throw this instead of setting the result string and return code

    The message should still be kept terse as the docs suggest
    '''
    pass

class NagiosCritical(Exception):
    '''
    See NagiosWarning
    '''
    pass

class PluginBase(object):
    '''
    Base class for plugin implementations.
    
    You don't have to actually use this...but it can't hurt!
    
    Subclass this and implement _run.
    '''
    
    VERSION = None
    DEFAULT_WARNING = None
    DEFAULT_CRITICAL = None

    def __init__(self, out_file=sys.stdout):
        self._output = OutputHandler(out_file)

        if self.DEFAULT_WARNING is None:
            self._warning = None
        else:
            self._warning = RangeThreshold(self.DEFAULT_WARNING)

        if self.DEFAULT_CRITICAL is None:
            self._critical = None
        else:
            self._critical = RangeThreshold(self.DEFAULT_CRITICAL)

        self._parser = get_option_parser(
            version=self.VERSION,
            out_file=self._output.file(),
            warning_range=self._warning,
            critical_range=self._critical,
        )

    def __call__(self, argv):
        opts = parse_options(self._parser, argv, output_handler=self._output)
        try:
            result = self._run(opts) or RESULT_OK
        except NagiosWarning, w:
            self._output.set_simple_result(str(w))
            self._output.display_and_exit(RESULT_WARNING)
        except NagiosCritical, c:
            self._output.set_simple_result(str(c))
            self._output.display_and_exit(RESULT_CRITICAL)
        except Exception, e:
            print >> self._output.file(), "Unexpected failure: %s" % (str(e))
            sys.exit(RESULT_UNKNOWN)
        else:
            self._output.display_and_exit(result)

    def _run(self, opts):
        '''
        Implement this method in your plugin.
        
        Execute your check, make calls to self._output (instance of OutputHandler)
        and then return your RESULT_ value.
        
        Be sure to call, at the very least, self._output.set_simple_result().
        
        You can also throw NagiosWarning or NagiosCritical to send a one-line message
        and exit with the appropriate error code if that is helpful.
        '''
        raise NotImplementedError