#!/usr/bin/python

from time import time
import stats
stats.starttime = time()
import sys
from frontends.console import Connection

if __name__ == "__main__":
    Connection().connect()
