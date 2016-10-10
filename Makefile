.PHONY: clean-pyc clean-build clean-skbuild docs clean

help:
	@echo "$(MAKE) [target]"
	@echo
	@echo "  targets:"
	@echo "    clean       - remove Python file and build artifacts"
	@echo "    lint        - check style with flake8"
	@echo "    test        - run tests quickly with the default Python"
	@echo "    test-all    - run tests on every Python version with tox"
	@echo "    coverage    - check code coverage quickly with the default Python"
	@echo "    docs        - generate Sphinx HTML documentation, including API docs"
	@echo "    dist        - package"
	@echo

clean: clean-build clean-pyc
	rm -fr htmlcov/
	find . -name '.coverage' -exec rm -f {} +
	find . -name 'coverage.xml' -exec rm -f {} +
	rm -rf .cache

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type f -name 'MANIFEST' -exec rm -f {} +
	rm -fr docs/_build

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8

test:
	python setup.py test

test-all:
	tox

coverage:
	coverage run --source skbuild setup.py test
	coverage report -m
	coverage html
	open htmlcov/index.html

docs-only:
	rm -f docs/ci rst
	rm -f docs/modules.rst
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

docs: docs-only
	open docs/_build/html/index.html || xdg-open docs/_build/html/index.html

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
