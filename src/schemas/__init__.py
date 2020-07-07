from pkg_resources import get_distribution, DistributionNotFound
import gettext
from pathlib import Path

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "Client_API_VN"
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:  # pragma: no cover
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound

# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("export_vn", str(localedir))
gettext.textdomain("export_vn")
_ = gettext.gettext
