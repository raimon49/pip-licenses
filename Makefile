REPO_NAME:=$(shell basename -s .git `git remote get-url origin`)
VENV_NAME:='venv/$(REPO_NAME)'
DEV_DEPENDS:='dev-requirements'

.DEFAULT_GOAL:= help
.PHONY: help, setup, local-install, local-uninstall, update-depends, lint, test, deploy, test-deploy, build, clean

help:
	@echo 'Usage: make <subcommand>'
	@echo ''
	@echo 'Subcommands:'
	@echo '    setup           Setup for development'
	@echo '    local-install   Install locally'
	@echo '    local-uninstall Uninstall locally'
	@echo '    update-depends  Re-compile requirements for development'
	@echo '    lint            Re-lint formatting and typing with pyproject.toml'
	@echo '    test            Run project tests'
	@echo '    deploy          Unused & Deprecated (Previously Release to PyPI server)'
	@echo '    test-deploy     Unused & Deprecated (previously released to Test PyPI server)'
	@echo '    build           Build package'
	@echo '    clean           Clean directories'

setup:
	test -d $(VENV_NAME) || python -m venv $(VENV_NAME)
	$(VENV_NAME)/bin/python -m pip install -r $(DEV_DEPENDS).txt

local-install:
	pip install -e .

local-uninstall:
	pip uninstall -y pip-licenses

update-depends:
	pip-compile --extra dev -o dev-requirements.txt -U pyproject.toml

lint:
	ruff check
	ruff format
	mypy --install-types --non-interactive .

test:
	pytest

deploy: build
	twine upload dist/*

test-deploy: build
	twine upload -r pypitest dist/*

build: clean
	python -m build

clean:
	rm -rf dist
