=============================
Contributing to Client_API_VN
=============================

Installing the environment
--------------------------

Note: install Debian development environment first::

    sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev
    sudo apt install git
    sudo apt install python-is-python3  
    sudo apt install python3-dev
    sudo apt install python3-venv

Add newer python versions, using pyenv::

    curl https://pyenv.run | bash
    pyenv install 3.7.7 # for example
    pyenv global 3.7.7  # for example

Create a python virtual environment, activate it and install or
update basic tools::

    python3 -m venv VN_env
    source VN_env/bin/activate
    python -m pip install --upgrade pip
    pip install --upgrade setuptools wheel twine babel tox coverage

Add the following lines to .bashrc, to enable pyenv and venv::

    # Activate venv
    source VN_env/bin/activate
    # Load pyenv automatically
    export PATH="~/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

Downloading source
------------------

Clone framagit repository::

    git clone https://framagit.org/lpo/Client_API_VN.git
    cd Client_API_VN
    git checkout develop

Installing the application
--------------------------

Run::

    ./setup.py develop
    ./setup.py install


Code changes
------------

Code changes must be related to an framagit issue. Any development, except
urgent patches, must be done on the develop branch.

The prefered editor is MS Visual Studio Code, with `blake` formating.

Each commit must include a reference to the framagit issue and must be
documented.
Changes are documented using towncrier (https://pypi.org/project/towncrier/).
To document a change :

1. Create a file in newsfragment, named `issue.type`, where:

    - `issue` is the framagit issue number
    - `type` describes the type of change:

        - `feature`: Signifying a new feature.
        - `bugfix`: Signifying a bug fix.
        - `doc`: Signifying a documentation improvement.
        - `removal`: Signifying a deprecation or removal of public API.
        - `misc`: A ticket has been closed, but it is not of interest to users.

2. Describe, for the users, the results of the change.
3. Commit this file with your changes.

Running the tests
-----------------

Create .evn_test.yaml file in your root directory, 
with actual data (site, user, password...)::

    transfer_vn --init .evn_test.yaml

The tests access the active production site of biolovision and
requires admin rights.

Currently, tests are only defined for the following sites::

    t07: https://www.faune-ardeche.org/
    t38: https://www.faune-isere.org/

Create the test database::

    transfer_vn --db_create .evn_test.yaml

Run tests (try one or the other, as I haven't found which one is best)::

    ./setup.py tests
    pytest

When tests are OK, run full test suite::

    tox

Test coverage and upload to codecov.io is possible, using tox targets clean and cover.

Updating translations
---------------------

If you added new text messages, enclosed in _(), you need to
update the translations::

    ./setup.py extract_messages
    ./setup.py update_catalog
    editor src/export_vn/locale/fr_FR/LC_MESSAGES/export_vn.po
    ./setup.py compile_catalog


Generating and uploading
------------------------

Generate CHANGELOG.rst from news fragment::

    LANG=C.UTF-8; towncrier build --name=Client-API-VN --version=vX.Y.Z

Commit pending changes and tag vX.Y.Z.

Generate distribution archives::

    ./setup.py clean --all
    rm dist/*
    ./setup.py sdist bdist_wheel

Upload to test.pypi::

    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

To test, install from test.pypi (until ready for PyPI)::

    pip install -i https://test.pypi.org/simple/ --extra https://pypi.org/simple Client-API-VN

Upload to pypi::

    twine upload dist/*

Building docker localy
----------------------

To build a local container::

    docker build --tag client-api-vn - < Dockerfile
