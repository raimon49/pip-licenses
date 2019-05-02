DEV_DEPENDS='dev-requirements'

.DEFAULT_GOAL:= help
.PHONY: help
help:
	@echo 'Usage: make <subcommand>'
	@echo ''
	@echo 'Subcommands:'
	@echo '    setup           Setup for development'
	@echo '    local-install   Install locally'
	@echo '    local-uninstall Uninstall locally'
	@echo '    update-depends  Re-compile requirements for development'
	@echo '    test            Run unittests'
	@echo '    deploy          Release to PyPI server'
	@echo '    test-deploy     Release to Test PyPI server'
	@echo '    build           Build package'
	@echo '    clean           Clean directories'

.PHONY: setup
setup:
	pip install -r $(DEV_DEPENDS).txt

.PHONY: local-install
local-install:
	pip install -e .

.PHONY: local-uninstall
local-uninstall:
	pip uninstall -y pip-licenses

.PHONY: update-depends
update-depends:
	pip-compile -U $(DEV_DEPENDS).in

.PHONY: test
test:
	python setup.py test

.PHONY: deploy
deploy: build
	twine upload dist/*

.PHONY: test-deploy
test-deploy: build
	twine upload -r pypitest dist/*

.PHONY: build
build: clean
	python setup.py sdist bdist_wheel

.PHONY: clean
clean:
	rm -rf dist
