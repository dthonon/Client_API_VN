=============================
Contributing to Client_API_VN
=============================

Installing the environment
--------------------------

Note: install Debian development environment first::

    sudo apt install build-essential
    sudo apt install python3.5-dev

Create a python virtual environment, activate it and install or
update basic tools::

    python3 -m venv VN_env
    source VN_env/bin/activate
    python -m pip install --upgrade pip
    pip install --upgrade setuptools wheel twine babel

Downloading source
------------------

Clone framagit repository::

    git clone https://framagit.org/lpo/Client_API_VN.git
    cd Client_API_VN
    git checkout develop

Running the tests
-----------------

Run tests::

    ./setup.py tests

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

Generating distribution archives::

    ./setup.py sdist bdist_wheel

Uploading to test.pypi::

    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

To test, install from test.pypi (until ready for PyPI)::

    pip install -i https://test.pypi.org/simple/ --extra https://pypi.org/simple Client-API-VN
