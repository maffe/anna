#!/usr/bin/env python

import glob
import sys
import unittest

def main():
    test_mods = [p[:-3] for p in glob.glob('test_*.py')]
    unittest.main(module=None, argv=sys.argv + test_mods)

if __name__ == "__main__":
    main()
