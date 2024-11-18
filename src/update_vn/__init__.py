import gettext
import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version("Client_API_VN")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("export_vn", str(localedir))
gettext.textdomain("export_vn")
_ = gettext.gettext
