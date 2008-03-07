#!/usr/bin/env python
"""Module used for testing the annarithmetic plugin."""

import csv
import os
import re
import sys

import jpype as j

USAGE = """
Usage:
    $ %s TEST_FILE

""" % sys.argv[0]

def start_JVM_from_curdir():
    path = os.path.join(os.path.abspath(os.curdir))
    cp = os.path.join("-Djava.class.path=%s" % path, "annarithmetic.jar")
    j.startJVM(j.getDefaultJVMPath(), cp)

def test(testfile):
    p = j.JPackage("annarithmetic").Plugin()
    i = 0
    passed = 0
    # OK, this is ugly, but I don't know a better way to get pretty output.
    prev_nl = False
    for test, solu in (l for l in csv.reader(testfile) if l):
        i += 1
        # Create a regular expression from this test. Changes "0.6`7" into
        # r"0\.6\d*7$". I.e.: "`" means "any number of digits".
        rsolu = "%s$" % re.escape(solu).replace(r"\`", r"\d*")
        result = p.processMessage(test)
        # .match() matches at the start of the string.
        if re.match(rsolu, result) is not None:
            sys.stdout.write("\rRunning tests... [%d/%d] OK" % (i, len(tests)))
            sys.stdout.flush()
            passed += 1
            prev_nl = False
        else:
            if not prev_nl:
                print
            print "FAIL: [%d/%d]:" % (i, len(tests)), repr(test), "returns",
            print "'%s', should be: '%s'" % (result, solu)
            prev_nl = True
    print "\rTest results:", passed, "of", len(tests), "passed."

def main():
    print __doc__
    try:
        filename = sys.argv[1]
    except IndexError:
        sys.exit(USAGE)
    test(open(filename))

if not j.isJVMStarted():
    start_JVM_from_curdir()

if __name__ == "__main__":
    main()
