=============================
Contributing to Client_API_VN
=============================

Note: install Debian development environment first::

    sudo apt install build-essential
    sudo apt install python3.5-dev

Create a python virtual environment, activate it and install or 
update basic tools::

    python3 -m venv VN_env
    source VN_env/bin/activate
    python -m pip install --upgrade pip
    pip install --upgrade setuptools wheel twine

Generating distribution archives::

    python setup.py sdist bdist_wheel


To test, install from test.pypi (until ready for PyPI)::

    pip install -i https://test.pypi.org/simple/ --extra https://pypi.org/simple export-vn
