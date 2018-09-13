RST_DOCS_DIR=docs/rst

.PHONY: clean clean-test clean-pyc clean-build docs help \
	dev/bumpversion-path dev/bumpversion-minor dev/bumpversion-major
.DEFAULT_GOAL := help


clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8
	flake8 ansible_galaxy_cli ansible_galaxy tests

test: ## run tests quickly with the default Python
	py.test

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source ansible_galaxy_cli -m pytest
	coverage report -m
	coverage html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f $(RST_DOCS_DIR)/ansible_galaxy_cli.rst
	rm -f $(RST_DOCS_DIR)/modules.rst
	sphinx-apidoc -o $(RST_DOCS_DIR) ansible_galaxy_cli
	$(MAKE) -C $(RST_DOCS_DIR) clean
	$(MAKE) -C $(RST_DOCS_DIR) html

dev/bumpversion-patch:
	bumpversion --verbose patch

dev/bumpversion-minor:
	bumpversion --verbose minor

dev/bumpversion-major:
	bumpversion --verbose major

dev/release: dist ## package and upload a release
	twine upload dist/*

dev/dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py install
