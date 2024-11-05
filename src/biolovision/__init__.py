import gettext
import importlib.metadata
from pathlib import Path

__version__ = "unknown"

try:
    __version__ = importlib.metadata.version("my_package_name")
except importlib.metadata.PackageNotFoundError:
    # Fall back on getting it from a local pyproject.toml.
    # This works in a development environment where the
    # package has not been installed from a distribution.
    import toml

    pyproject_toml_file = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_toml_file.exists() and pyproject_toml_file.is_file():
        __version__ = toml.load(pyproject_toml_file)["tool"]["poetry"]["version"]
        # Indicate it might be locally modified or unreleased.
        __version__ = __version__ + "+"

# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("export_vn", str(localedir))
gettext.textdomain("export_vn")
_ = gettext.gettext
