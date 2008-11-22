#!/usr/bin/env python
"""Module used for testing the annai calc plugin."""

import csv
import os
import re
import sys

import calc

USAGE = """
Usage:
    $ %s TEST_FILE

""" % sys.argv[0]

def test(testfile):
    tests = [l for l in csv.reader(testfile) if l]
    pars = calc.MyParser()
    i = 0
    passed = 0
    for test, solu in tests:
        i += 1
        # Create a regular expression from this test. Changes "0.6`7" into
        # r"0\.6\d*7$". I.e.: "`" means "any number of digits".
        rsolu = "%s$" % re.escape(solu).replace(r"\`", r"\d*")
        try:
            (success, res) = pars.parse(test)
        except ArithmeticError:
            success = res = 0
        result = "%g" % res if success else ''
        # .match() matches at the start of the string.
        if re.match(rsolu, result) is not None:
            sys.stdout.write("\rRunning tests... [%d/%d] OK" % (i, len(tests)))
            sys.stdout.flush()
            passed += 1
        else:
            print "\rFAIL: [%d/%d]:" % (i, len(tests)), repr(test), "returns",
            print "'%s', should be: '%s'" % (result, solu)
    print "\rTest results:", passed, "of", len(tests), "passed."

def main():
    print __doc__
    try:
        filename = sys.argv[1]
    except IndexError:
        sys.exit(USAGE)
    test(open(filename))

if __name__ == "__main__":
    main()
