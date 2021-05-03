PYTHON=python3
PORT=8297
ENV_DIR=.env_$(PYTHON)

ifeq ($(OS),Windows_NT)
	IN_ENV=. $(ENV_DIR)/Scripts/activate &&
else
	IN_ENV=. $(ENV_DIR)/bin/activate &&
endif

BUILD_ENV = $(IN_ENV) PYTHONOPTIMIZE=1 &&

all: test lint artifacts

$(ENV_DIR):
	virtualenv -p $(PYTHON) $(ENV_DIR)

env: $(ENV_DIR)

artifacts: build-reqs sdist

$(NODE_DIR):
	$(NODE_INSTALL)

build-reqs: env
	$(IN_ENV) pip install black

package_reqs: env
	$(IN_ENV) pip install pyinstaller

build: build-reqs
	$(IN_ENV) pip install --editable .

sdist: build-reqs
	$(IN_ENV) python setup.py sdist

lint: flake8

flake8: build-reqs
	- $(IN_ENV) flake8 src/harren > flake8.out

shell: build-reqs build
	- $(IN_ENV) python

freeze: env
	- $(IN_ENV) pip freeze

prod: build
	$(IN_ENV) harren --fullscreen

run: build
	$(IN_ENV) harren --no-splash

run-debug: build
	$(IN_ENV) harren -l DEBUG --no-splash --no-sound

run-fs: build
	$(IN_ENV) harren --fullscreen --no-splash

run-splash: build
	$(IN_ENV) harren -l DEBUG

package: package_reqs
	$(BUILD_ENV) pyinstaller src/harren/entry_point.py --hidden-import pygame --hidden-import log-color --hidden-import six --hidden-import toml --hidden-import boltons -p src/harren --add-data "src/harren:harren" --name harren --onefile --noconsole

format-code:
	$(IN_ENV) black -l 119 src/ tests/ setup.py

check-code:
	$(IN_ENV) black --check -l 119 src/ tests/ setup.py

help: build
	$(IN_ENV) harren -h

clean:
	- @rm -rf BUILD
	- @rm -rf BUILDROOT
	- @rm -rf RPMS
	- @rm -rf SRPMS
	- @rm -rf SOURCES
	- @rm -rf docs/build
	- @rm -rf src/*.egg-info
	- @rm -rf build
	- @rm -rf dist
	- @rm -f .coverage
	- @rm -f test_results.xml
	- @rm -f coverage.xml
	- @rm -f pep8.out
	- @rm -f .coverage*
	- @rm -rf tmp.json
	- @find . -name '*.orig' -delete
	- @find . -name '*.DS_Store' -delete
	- @find . -name '*.pyc' -delete
	- @find . -name '*.pyd' -delete
	- @find . -name '*.pyo' -delete
	- @find . -name '*__pycache__*' -delete
	- @rm -rf src/harren/dist
	- @rm -rf src/harren/build
	- @rm -rf src/harren/entry_point.spec

env-clean: clean
	- @rm -rf $(ENV_DIR)
	- @rm -rf $(INSTALL_ENV_DIR)
	- @rm -rf .env*
	- @rm -rf .install_env
	- @rm -rf node_modules
	- @rm -rf tmp.json
