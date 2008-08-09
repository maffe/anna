PYTHONPATH := ../src:$(PYTHONPATH)
PYTHON = python
PYTHONARGS = -tt
TESTARGS = 
TESTALL = testall.py
TESTS = $(wildcard test_*.py)

.PHONY: $(TESTALL) test
$(TESTALL) test:
	$(PYTHON) $(PYTHONARGS) $(TESTALL) $(TESTARGS)

.PHONY: $(TESTS) seperate
$(TESTS):
	$(PYTHON) $(PYTHONARGS) $@ $(TESTARGS)
# Run all test suites seperately.
seperate: $(TESTS)

.PHONY: clean
clean:
	-\rm -f *.pyc *.pyo
