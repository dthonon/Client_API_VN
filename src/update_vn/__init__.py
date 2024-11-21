import gettext
import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version("Client_API_VN")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

# Install gettext for any file in the application
localedir = str(Path(__file__).resolve().parent / "locale")
# lang2 = gettext.translation("update_vn", localedir=localedir, languages=["fr_FR"])
# lang2.install()
gettext.install("update_vn", localedir=localedir)
