poetry.lock: pyproject.toml
	@echo "🚀 Updating lockfile"
	poetry lock

.PHONY: install
install: poetry.lock ## Install the poetry environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@poetry install
	@poetry run pre-commit install
	@poetry shell

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@poetry run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@poetry run mypy
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@poetry run deptry .

update_catalog: ec_biolovision ec_export_vn ec_schemas ec_update_vn ## Compile translation catalogs

ec_biolovision: src/biolovision/*.py
	pybabel extract src/biolovision/ --output-file=src/biolovision/locale/biolovision.pot --no-wrap \
	--msgid-bugs-address=d.thonon9@outlook.com --copyright-holder="Daniel Thonon" --project=Client_API_VN
	pybabel update --input-file=src/biolovision/locale/biolovision.pot --domain=biolovision \
	--output-dir=src/biolovision/locale/ --update-header-comment

ec_export_vn: src/export_vn/*.py
	pybabel extract src/export_vn/ --output-file=src/export_vn/locale/export_vn.pot --no-wrap \
	--msgid-bugs-address=d.thonon9@outlook.com --copyright-holder="Daniel Thonon" --project=Client_API_VN
	pybabel update --input-file=src/export_vn/locale/export_vn.pot --domain=export_vn \
	--output-dir=src/export_vn/locale/ --update-header-comment

ec_schemas: src/schemas/*.py
	pybabel extract src/schemas/ --output-file=src/schemas/locale/schemas.pot --no-wrap \
	--msgid-bugs-address=d.thonon9@outlook.com --copyright-holder="Daniel Thonon" --project=Client_API_VN
	pybabel update --input-file=src/schemas/locale/schemas.pot --domain=schemas \
	--output-dir=src/schemas/locale/ --update-header-comment

ec_update_vn: src/update_vn/*.py
	pybabel extract src/update_vn/ --output-file=src/update_vn/locale/update_vn.pot --no-wrap \
	--msgid-bugs-address=d.thonon9@outlook.com --copyright-holder="Daniel Thonon" --project=Client_API_VN
	pybabel update --input-file=src/update_vn/locale/update_vn.pot --domain=update_vn \
	--output-dir=src/update_vn/locale/ --update-header-comment

compile_catalog: cc_biolovision cc_export_vn cc_update_vn ## Compile translation catalogs

cc_biolovision:
	pybabel compile --domain=biolovision --directory=src/biolovision/locale/

cc_export_vn:
	pybabel compile --domain=export_vn --directory=src/export_vn/locale/

cc_update_vn:
	pybabel compile --domain=update_vn --directory=src/update_vn/locale/

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest not slow"
	@poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml -m "not slow"

.PHONY: test_slow
test_slow: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml

# Integration tests: live VisioNature API + PostGIS database.
# Need a running Postgres/PostGIS on $(DB_HOST):$(DB_PORT) (see docker-compose.yml)
# and the VN_* credentials exported in the environment:
#   VN_SITE_URL VN_USER_EMAIL VN_USER_PW VN_CLIENT_KEY VN_CLIENT_SECRET
# Remote-write tests stay disabled unless VN_ENABLE_WRITE_TESTS=1 (tests/conftest.py).
DB_HOST ?= localhost
DB_PORT ?= 5432
DB_NAME ?= faune_test
DB_GROUP ?= lpo_test
DB_USER ?= xfer38
DB_PW ?= xfer38pw
PGPASSWORD ?= postgres
PYTEST_MARKERS ?= not slow and not privileged
export DB_HOST DB_PORT DB_NAME DB_GROUP DB_USER DB_PW

# Variables substituted into the test configuration templates by envsubst.
ENVSUBST_VARS = $${VN_SITE_URL} $${VN_USER_EMAIL} $${VN_USER_PW} $${VN_CLIENT_KEY} $${VN_CLIENT_SECRET} $${DB_HOST} $${DB_PORT} $${DB_NAME} $${DB_GROUP} $${DB_USER} $${DB_PW}

.PHONY: test-config
test-config: ## Render ~/.evn_test.{yaml,toml} from templates and VN_*/DB_* env vars
	@echo "🚀 Rendering test configuration from templates"
	@envsubst '$(ENVSUBST_VARS)' < tests/data/evn_test.yaml.tmpl > $$HOME/.evn_test.yaml
	@envsubst '$(ENVSUBST_VARS)' < tests/data/evn_test.toml.tmpl > $$HOME/.evn_test.toml

.PHONY: test-db
test-db: ## Enable PostGIS extensions + app role, then create the database and tables
	@echo "🚀 Setting up the test database"
	@PGPASSWORD=$(PGPASSWORD) psql -h $(DB_HOST) -p $(DB_PORT) -U postgres -d postgres -f docker/init-db.sql
	@poetry run transfer_vn --db_drop --db_create --json_tables_create --col_tables_create .evn_test.yaml

.PHONY: test-integration
test-integration: test-config test-db ## Render config, set up DB and run the integration suite
	@echo "🚀 Running integration tests: pytest -m \"$(PYTEST_MARKERS)\""
	@poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml -m "$(PYTEST_MARKERS)"

.PHONY: test-integration-docker
test-integration-docker: ## Run the integration suite inside the docker compose dev stack
	@echo "🚀 Running integration tests inside the docker compose stack"
	@docker compose up -d --build
	@docker compose exec -w /code \
		-e VN_SITE_URL="$$VN_SITE_URL" -e VN_USER_EMAIL="$$VN_USER_EMAIL" -e VN_USER_PW="$$VN_USER_PW" \
		-e VN_CLIENT_KEY="$$VN_CLIENT_KEY" -e VN_CLIENT_SECRET="$$VN_CLIENT_SECRET" \
		app make test-config DB_HOST=db
	@docker compose exec -w /code app sh -c 'PGPASSWORD=$(PGPASSWORD) psql -h db -p 5432 -U postgres -d postgres -f docker/init-db.sql'
	@# transfer_vn and pytest must run from /root: the config file name is passed
	@# to Dynaconf as a relative path, searched upward from the current directory,
	@# and /code is not under /root.
	@docker compose exec -w /root app transfer_vn --db_drop --db_create --json_tables_create --col_tables_create .evn_test.yaml
	@docker compose exec -w /root app pytest /code/tests -m "$(PYTEST_MARKERS)"

.PHONY: test-regression
test-regression: ## Run the mocked incremental-download regression tests (PostGIS, no account)
	@echo "🚀 Enabling extensions and the application role"
	@PGPASSWORD=$(PGPASSWORD) psql -h $(DB_HOST) -p $(DB_PORT) -U postgres -d postgres -f docker/init-db.sql
	@echo "🚀 Running regression tests"
	@poetry run pytest tests/test_increment_regression.py

.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	@poetry publish --dry-run
	@echo "🚀 Publishing."
	@poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@poetry run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@poetry run mkdocs serve

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
