.PHONY: all
all: dependencies

.PHONY: dependencies
dependencies: dependencies/pyparsing.py

dependencies/pyparsing.py: dependencies/pyparsing-svn/
	cd dependencies/pyparsing-svn/src ; \
	python setup.py install_lib --install-dir ../../ --force
