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
