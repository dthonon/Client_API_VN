
![Logo](img/logo_vn2pg.png)

# Client_API_VN

[![Release](https://img.shields.io/github/v/release/dthonon/Client_API_VN)](https://github.com/dthonon/Client_API_VN/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/dthonon/Client_API_VN/main.yml?branch=main)](https://github.com/dthonon/Client_API_VN/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/dthonon/Client_API_VN)](https://github.com/dthonon/Client_API_VN/graphs/commit-activity)
[![codecov](https://codecov.io/gh/dthonon/Client_API_VN/branch/main/graph/badge.svg)](https://codecov.io/gh/dthonon/Client_API_VN)
[![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/dthonon/Client_API_VN)](https://github.com/dthonon/Client_API_VN/issues)
[![License](https://img.shields.io/github/license/dthonon/Client_API_VN)](https://github.com/dthonon/Client_API_VN/blob/main/LICENSE)

## Presentation

Python applications that use Biolovision/VisioNature (VN) API to:

- download data from VN sites and stores it to a Postgresql database.
- update sightings directly in VN site

Applications are available either as:

- Python modules from PyPI
- Docker images from Docker Hub

They are tested under Linux Ubuntu >20 or Debian 10. Other Linux
distributions could work. Windows is not tested at all and will
probably not work.

- **Github repository**: <https://github.com/dthonon/Client_API_VN/>
- **Documentation** <https://dthonon.github.io/Client_API_VN/>

A thin Python layer on top of Biolovision API is provided, as described in
[biolovision.api](modules.md).

### Installation - Python

These instructions present the steps required to install the
Python applications.

Windows:

    Install Python from Microsoft store

    Add python script directory to Path, as described in
    `How to add Python to Windows PATH <https://datatofish.com/add-python-to-windows-path/>`_.

Linux: add the following debian packages:

    sudo apt -y install build-essential python3-dev python3-venv

Create a python virtual environment, activate it and update basic tools:

    python3 -m venv env_VN
    source env_VN/bin/activate
    python -m pip install --upgrade pip

Install from PyPI:

    pip install Client-API-VN

### Installation - Docker

These instructions present the steps required to install the
Docker applications:

    docker pull dthonon/client-api-vn
    docker run --name xfer_vn \
               --mount source=xfer_vn,target=/root \
               --workdir /root \
               --tty --interactive \
               dthonon/client-api-vn bash

This docker only contains the application and requires an external
Postgresql database.

The following steps are the common to both Python and Docker installation.

### Getting Started - transfer_vn

See [transfer_vn](apps/transfer_vn.md) for more information.

### Getting Started - update_vn

See [update_vn](apps/update_vn.md) for more information.

### Getting Started - validate_vn

See [validate_vn](apps/validate_vn.md) for more information.

### Prerequisites

For Linux and Postgresql installation, refer to [server installation](apps/server_install.md).

Installation requires the following python module:

```bash
pip
```

All other python dependencies are managed by `make install`.

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
