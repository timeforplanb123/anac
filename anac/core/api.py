import httpx
import re
from pydantic.dataclasses import dataclass
from typing import Dict, Any, TypeVar
from .exceptions import raise_for_status
from .endpoint import Endpoint

A = TypeVar("A", bound="Api")


@dataclass
class Api:
    """The initial API object.

    Run openapi() coroutine/method to pull down openapi spec
    and dynamically creates attributes/endpoints.
    After that you can use 'tab' autocompletion
    in python interpreter

    Args:
        url (str): NetBox url
        token (str): NetBox API token

    Returns:
        Api object

    Raises:
        TypeError: If you forgot to specify 'url' or 'token' argument

    Usage:
        In [1]: from anac import api
           ...:
           ...: a = api(
           ...:     "https://your_netbox",
           ...:     token="your_api_token",
           ...: )
           ...: await a.openapi()
    """
    url: str
    token: str

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __post_init_post_parse__(self) -> None:

        self.http_session = httpx.AsyncClient()

        self.base_url = f"{self.url if self.url[-1] != '/' else self.url[:-1]}/api"

    async def get_openapi(self, timeout: float) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json;",
        }
        req = await self.http_session.get(
            f"{self.base_url}/docs/?format=openapi",
            headers=headers,
            timeout=timeout,
        )

        raise_for_status(req)

        return req.json()

    async def openapi(self, timeout: float = 50.0) -> None:
        """Get openapi spec and create attributes/endpoints
        with python interpreter autocompletion

        Args:
            timeout (float): Timeout for openapi http request

        Returns:
            N/A

        Raises:
            httpx.HTTPStatusError, httpx.ConnectError:
                See https://github.com/encode/httpx/blob/master/httpx/_exceptions.py
            json.JSONDecodeError: NetBox returns non json data

        Usage:
            In [1]: from anac import api
               ...:
               ...: a = api(
               ...:     "https://netbox",
               ...:     token="api_token",
               ...: )
               ...: await a.openapi()
        """
        self.open_api = await self.get_openapi(timeout=timeout)

        for endpoint in self.open_api["paths"].keys():
            setattr(
                self,
                re.sub(r"[-/]", "_", re.sub(r"[{}]", "", endpoint[1:-1])),
                Endpoint(self, self.base_url, endpoint),
            )

    async def aclose(self) -> None:
        """Close httpx.AsyncClient()

        Usage:
            In [1]: from anac import api
               ...:
               ...: a = api(
               ...:     "http://netbox",
               ...:     token="api_token",
               ...: )
               ...: await a.openapi()
               ...:

            In [2]: await a.aclose()
        """
        await self.http_session.aclose()

    async def __aenter__(self: A) -> A:
        """Use Api as a context manager

        Usage:
            In [1]: from anac import api
               ...:
               ...: async with api(
               ...:     "http://netbox",
               ...:     token="api_token",
               ...: ) as a:
               ...:     test1_device = await a.dcim_devices(get={"name": "test1"})

            In [2]: test1_device
            Out[2]: EndpointId(api=Api, url='http://your_netbox/api',
            endpoint='/dcim/devices/')
        """
        await self.openapi()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.http_session.aclose()
