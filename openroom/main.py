# Copyright (c) 2009 Brian Zimmer <bzimmer@ziclix.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
from optparse import OptionParser
from openroom import lightroom, reports

def main(args=None):

    p = OptionParser()
    p.add_option("-v", "--verbose", default=False, action="store_true", help="display sql")
    opts, args = p.parse_args(args=args)

    if not args:
        p.exit(1, "\nno Lightroom database found\n")

    for arg in args:
        lr = reports.Reports(lightroom(arg, opts.verbose))
        print "# focal lengths"
        for a in lr.focalLengths():
            print a
        print "# image counts"
        for a in lr.imageCounts():
            print a
        print "# crops"
        for a in (None, True, False):
            print "# picks", a
            for b in lr.crops(a):
                print b

