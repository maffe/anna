#!/usr/bin/env python
#TODO: Interpret ` as wildcard.
"""Test the Annarithmetic plugin.

Usage:
    test.py TEST_FILE

"""
import csv
import os
import sys

import jpype as j

def start_JVM_from_curdir():
    path = os.path.join(os.path.abspath(os.curdir))
    cp = os.path.join("-Djava.class.path=%s" % path, "annarithmetic.jar")
    j.startJVM(j.getDefaultJVMPath(), cp)

def test(testfile):
    p = j.JPackage("annarithmetic").Plugin()
    tests = [l for l in csv.reader(testfile) if l]
    i = 0
    passed = 0
    # OK, this is ugly, but I don't know a better way to get pretty output.
    prev_nl = False
    for test, sol in tests:
        i += 1
        result = p.processMessage(test)
        if result == sol:
            sys.stdout.write("\rRunning tests... [%d/%d] OK" % (i, len(tests)))
            sys.stdout.flush()
            passed += 1
            prev_nl = False
        else:
            if not prev_nl:
                print
            print "FAIL: [%d/%d]:" % (i, len(tests)), repr(test), "returns",
            print "'%s', should be: '%s'" % (result, sol)
            prev_nl = True
    print "\rTest results:", passed, "of", len(tests), "passed."

def main():
    try:
        test(open(sys.argv[1]))
    except IndexError:
        print >> sys.stderr, __doc__

if not j.isJVMStarted():
    start_JVM_from_curdir()

if __name__ == "__main__":
    main()
