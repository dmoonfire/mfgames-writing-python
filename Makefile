PYTHON_FILES = $(shell grep '.py' setup.py | grep -v 'bin/env' | cut -f 2 -d "'")
PYTHON_NAMESPACES = $(shell grep '.py' setup.py | grep -v 'bin/env' | cut -f 2 -d "'" | sed 's@/__init__.py@@' | sed 's@.py@@' | sed 's@/@.@g' | cut -c 5-)

all:

install:
	python setup.py install

clean:
	find -name "*.pyc" -o -name "*~" -print0 | xargs -0 rm -f

check:
	PYTHONPATH=src PYTHONVER=2.6 pylint \
		--reports=no --include-ids=yes \
		$(PYTHON_FILES)