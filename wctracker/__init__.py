"""wctracker — live WC2026 group-stage advancement probability tracker."""
import warnings

# Quieten the cosmetic LibreSSL/urllib3 warning seen on stock macOS Python.
warnings.filterwarnings("ignore", message=r".*OpenSSL.*", module="urllib3")

__version__ = "0.1.0"
