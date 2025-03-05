# Contributing to `Client_API_VN`

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/dthonon/Client_API_VN/issues

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

### Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Client_API_VN could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/dthonon/Client_API_VN/issues.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `Client_API_VN` for local development.
Please note this documentation assumes you already have `poetry` and `Git` installed and ready to go.

### Installing the environment
Note: install Ubuntu development environment first:
```bash
sudo apt install git build-essential zlib1g-dev libncurses5-dev libgdbm-dev
sudo apt install libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev
sudo apt install python-is-python3 python3-dev python3-venv
```

Add newer python versions, using `pyenv`:
```bash
curl https://pyenv.run | bash
pyenv install 3.10.8 # for example
pyenv global 3.10.8  # for example
```
If you are using `pyenv`, select a version to use locally. (See installed versions with `pyenv versions`)

```bash
pyenv local <x.y.z>
```

Add the following lines to .bashrc, to enable pyenv:
```bash
# Load pyenv automatically
export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

### Downloading source
Clone github repository:
```bash
git clone https://github.com/dthonon/Client_API_VN.git
cd Client_API_VN
```

### Installing the application
Run:
```bash
poetry install
```

### Code changes
Install pre-commit to run linters/formatters at commit time:
```bash
poetry run pre-commit install
```

Create a branch for local development:
```bash
git checkout -b name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

When you're done making changes, check that your changes pass the formatting tests.
```bash
make check
```

### Running the tests
Don't forget to add test cases for your added functionality to the `tests` directory.

Create .evn_test.toml file in your root directory:
```bash
transfer_vn --init .evn_test.toml
```
Replace template text with actual data (site, user, password...).
The tests access the active production site of biolovision and requires admin rights.

Currently, tests are only defined for the following sites:
```
tff: https://www.faune-aura.org/
```
Create the test database::
```bash
transfer_vn --db_create .evn_test.yaml
```

Now, validate that all unit tests are passing:
```bash
make test
```

Before raising a pull request you should also run tox.
This will run the tests across different versions of Python:
```bash
tox
```

This requires you to have multiple versions of python installed.
This step is also triggered in the CI/CD pipeline, so you could also choose to skip this step locally.

### Update translations
If you added new text messages, enclosed in _(), you need to update the translations:
```bash
make update_catalog
editor src/export_vn/locale/fr_FR/LC_MESSAGES/export_vn.po
make compile_catalog
```

### Finalize changes
Commit your changes and push your branch to GitHub:

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

Submit a pull request through the GitHub website.

#### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated.
   Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.
