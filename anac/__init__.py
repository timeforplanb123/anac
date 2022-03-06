from pkg_resources import get_distribution, DistributionNotFound
from anac.core.api import Api as api
from anac.core.exceptions import (
    RequestDataError,
    RequestParamsError,
    raise_for_status,
)

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass

__all__ = ("api", "RequestDataError", "RequestParamsError", "raise_for_status")
