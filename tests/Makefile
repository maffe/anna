PYTHONPATH := ../src:$(PYTHONPATH)
PYTHON = python2.5
PYTHONARGS := -tt $(PYTHONARGS)
TESTARGS := $(TESTARGS)
TESTALL = testall.py
TESTS = $(wildcard test_*.py)

.PHONY: $(TESTALL) test
$(TESTALL) test: clean
	$(PYTHON) $(PYTHONARGS) $(TESTALL) $(TESTARGS)
# Optimized versions must be tested too.
	$(PYTHON) -O $(PYTHONARGS) $(TESTALL) $(TESTARGS)

.PHONY: $(TESTS) seperate
$(TESTS):
	$(PYTHON) $(PYTHONARGS) $@ $(TESTARGS)
	$(PYTHON) -O $(PYTHONARGS) $@ $(TESTARGS)
# Run all test suites seperately.
seperate: clean $(TESTS)

.PHONY: quiet verbose
quiet: clean
	$(PYTHON) $(PYTHONARGS) $(TESTALL) -q $(TESTARGS)
	$(PYTHON) -O $(PYTHONARGS) $(TESTALL) -q $(TESTARGS)
verbose: clean
	$(PYTHON) $(PYTHONARGS) $(TESTALL) -v $(TESTARGS)
	$(PYTHON) -O $(PYTHONARGS) $(TESTALL) -v $(TESTARGS)

.PHONY: clean
clean:
	-rm -f *.pyc *.pyo
	$(MAKE) -C ../src clean
