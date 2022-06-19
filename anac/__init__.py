from importlib.metadata import PackageNotFoundError, version

from anac.core.api import Api as api
from anac.core.exceptions import (
    raise_for_status,
    RequestDataError,
    RequestParamsError,
)

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ("api", "RequestDataError", "RequestParamsError", "raise_for_status")
