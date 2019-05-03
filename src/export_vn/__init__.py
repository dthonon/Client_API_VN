import gettext
from pathlib import Path

# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / 'locale'
gettext.install('transfer_vn', str(localedir))
# t = gettext.translation('transfer_vn', str(localedir), fallback=True)
# _ = t.gettext
