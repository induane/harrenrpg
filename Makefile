PYTHON=python3
PORT=8297
ENV_DIR=.env_$(PYTHON)

ifeq ($(OS),Windows_NT)
	IN_ENV=. $(ENV_DIR)/Scripts/activate &&
else
	IN_ENV=. $(ENV_DIR)/bin/activate &&
endif

all: test lint artifacts

$(ENV_DIR):
	virtualenv -p $(PYTHON) $(ENV_DIR)

env: $(ENV_DIR)

artifacts: build_reqs sdist

$(NODE_DIR):
	$(NODE_INSTALL)

build_reqs: env
	$(IN_ENV) pip install unify

build: build_reqs
	$(IN_ENV) pip install --editable .

sdist: build_reqs
	$(IN_ENV) python setup.py sdist

lint: flake8

flake8: build_reqs
	- $(IN_ENV) flake8 src/harren > flake8.out

shell: build_reqs build
	- $(IN_ENV) python

freeze: env
	- $(IN_ENV) pip freeze

unify: build_reqs
	- $(IN_ENV) unify --in-place --recursive src/

prod: build
	$(IN_ENV) harren --fullscreen

run:
	$(IN_ENV) harren --no-splash

run-debug:
	$(IN_ENV) harren -l DEBUG --no-splash

run-fs:
	$(IN_ENV) harren --fullscreen --no-splash

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
	- @find . -name '*.pyc' -delete
	- @find . -name '*.pyd' -delete
	- @find . -name '*.pyo' -delete
	- @find . -type d -name '__pycache__' -delete
	- @rm -rf src/harren/dist
	- @rm -rf src/harren/build
	- @rm -rf src/harren/entry_point.spec

env_clean: clean
	- @rm -rf $(ENV_DIR)
	- @rm -rf $(INSTALL_ENV_DIR)
	- @rm -rf .env*
	- @rm -rf .install_env
	- @rm -rf node_modules
	- @rm -rf tmp.json
