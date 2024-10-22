# Client_API_VN

[![Release](https://img.shields.io/github/v/release/dthonon/Client_API_VN)](https://img.shields.io/github/v/release/dthonon/Client_API_VN)
[![Build status](https://img.shields.io/github/actions/workflow/status/dthonon/Client_API_VN/main.yml?branch=main)](https://github.com/dthonon/Client_API_VN/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/dthonon/Client_API_VN/branch/main/graph/badge.svg)](https://codecov.io/gh/dthonon/Client_API_VN)
[![Commit activity](https://img.shields.io/github/commit-activity/m/dthonon/Client_API_VN)](https://img.shields.io/github/commit-activity/m/dthonon/Client_API_VN)
[![License](https://img.shields.io/github/license/dthonon/Client_API_VN)](https://img.shields.io/github/license/dthonon/Client_API_VN)

This is a template repository for Python projects that use Poetry for their dependency management.

- **Github repository**: <https://github.com/dthonon/Client_API_VN/>
- **Documentation** <https://dthonon.github.io/Client_API_VN/>

## Getting started with your project


Finally, install the environment and the pre-commit hooks with

```bash
make install
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI or Artifactory, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/codecov/).

## Releasing a new version

- Create an API Token on [PyPI](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting [this page](https://github.com/dthonon/Client_API_VN/settings/secrets/actions/new).
- Create a [new release](https://github.com/dthonon/Client_API_VN/releases/new) on Github.
- Create a new tag in the form `*.*.*`.
- For more details, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/cicd/#how-to-trigger-a-release).

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
