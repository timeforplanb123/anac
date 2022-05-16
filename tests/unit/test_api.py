import pytest
from unittest.mock import AsyncMock
import re
import os
import pickle
from httpx import ConnectError, HTTPStatusError
from json import JSONDecodeError
from anac import api
from anac.core.endpoint import Endpoint


@pytest.fixture
def openapi_spec():
    openapi_spec = {
        "swagger": "2.0",
        "info": {
            "title": "NetBox API",
            "description": "API to access NetBox",
            "termsOfService": "https://github.com/netbox-community/netbox",
            "license": {"name": "Apache v2 License"},
            "version": "3.2",
        },
        "host": "demo.netbox.dev",
        "schemes": ["https"],
        "basePath": "/api",
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
            }
        },
        "security": [{"Bearer": []}],
        "paths": {
            "/circuits/circuit-terminations/": {
                "get": {},
                "post": {},
                "put": {},
                "patch": {},
                "delete": {},
            }
        },
    }
    return openapi_spec


@pytest.fixture(scope="module")
def anac_api():
    a = api("https://demo.netbox.dev", token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c")
    yield a


@pytest.fixture
def mock_get_openapi(mocker, openapi_spec):
    async_mock = AsyncMock(return_value=openapi_spec)
    mocker.patch("anac.api.get_openapi", side_effect=async_mock)


@pytest.fixture
def httpx_response():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".httpx_response")
    with open(path, "rb") as f:
        response = pickle.load(f)
    return response


@pytest.fixture
def mock_httpx_asyncclient_get(mocker):
    def _mock_httpx_asyncclient_get(response):
        mock = mocker.patch("httpx.AsyncClient.get")
        mock.return_value = response
        return mock

    return _mock_httpx_asyncclient_get


@pytest.mark.parametrize("url", ["https://demo.netbox.dev", "https://demo.netbox.dev/"])
async def test_attributes(anac_api, mock_get_openapi, url):
    assert anac_api.base_url == "https://demo.netbox.dev/api"


@pytest.mark.asyncio
async def test_openapi(anac_api, mock_get_openapi):
    await anac_api.openapi()
    assert "paths" in anac_api.open_api
    assert isinstance(anac_api.open_api["paths"], dict)

    endpoint_key = list(anac_api.open_api["paths"])[0]
    assert isinstance(endpoint_key, str)

    endpoint_key = re.sub(r"[-/]", "_", re.sub(r"[{}]", "", endpoint_key[1:-1]))
    endpoint = getattr(anac_api, endpoint_key, None)
    assert isinstance(endpoint, Endpoint)


def test_repr(anac_api):
    assert repr(anac_api) == "Api"


@pytest.mark.asyncio
async def test_context_manager(mock_get_openapi):
    async with api(
        "https://demo.netbox.dev", token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c"
    ) as a:
        pass

    assert "paths" in a.open_api
    assert isinstance(a, api)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kwargs", "arg", "value", "exc"),
    [
        (
            {
                "url": "https://demo.netbox.devv",
                "token": "cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
            },
            None,
            None,
            ConnectError,
        ),
        ({"token": "cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c"}, None, None, TypeError),
        (
            {
                "url": "https://demo.netbox.dev",
                "token": "cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
            },
            "status_code",
            403,
            HTTPStatusError,
        ),
        (
            {
                "url": "https://demo.netbox.dev",
                "token": "cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
            },
            "_content",
            b"test123",
            JSONDecodeError,
        ),
    ],
)
async def test_anac_api_exceptions(
    httpx_response, mock_httpx_asyncclient_get, kwargs, arg, value, exc
):
    if arg:
        setattr(httpx_response, arg, value)
        mock_httpx_asyncclient_get(httpx_response)
    with pytest.raises(exc) as exc:
        if ".devv" in httpx_response.url.host:
            raise ConnectError("[Errno -2] Name or service not known")
        a = api(**kwargs)
        await a.openapi(timeout=1.0)
