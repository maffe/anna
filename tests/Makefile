PYTHONPATH := ../src/:$(PYTHONPATH)
PYTHON = python
PYTHONARGS = -tt
TESTARGS = -q
# Files starting with _ are not considered tests.
TESTS = $(addprefix test_, $(basename $(wildcard [^_]*.py)))

.PHONY: test
test: $(TESTS)

.PHONY: $(TESTS)
$(TESTS):
	$(PYTHON) $(PYTHONARGS) $(subst test_, , $@).py $(TESTARGS)
