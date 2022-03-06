import httpx
import re
import dataclasses
from pydantic import (
    BaseModel,
    validator,
)
from typing import (
    Dict,
    List,
    Union,
    Any,
    TYPE_CHECKING,
    TypeVar,
    Coroutine,
    Iterator,
)
from json import JSONDecodeError
from itertools import zip_longest
from .exceptions import RequestParamsError, RequestDataError, raise_for_status

if TYPE_CHECKING:
    from .api import Api

E = Union["EndpointId", "EndpointIdIterator"]
T = TypeVar("T")

KwargsType = Dict[str, Union[List[Dict[str, Any]], Dict[str, Any]]]
KwargsDict = Dict[str, Dict[str, Any]]


@dataclasses.dataclass
class EndpointBase:
    api: "Api"
    url: str
    endpoint: str

    async def _request(self, kwargs: Dict[str, Any]) -> httpx.Response:
        action = [*kwargs][0]
        endpoint = self.endpoint

        if action == "get":
            params = {
                "headers": {
                    "authorization": f"Token {self.api.token}",
                    "accept": "application/json;",
                },
                "params": kwargs[action],
            }
            err = RequestParamsError(
                f"{action.upper()} method must contain object id"
                ' in the {"id": 1} format',
            )
        else:
            params = {
                "headers": {
                    "authorization": f"Token {self.api.token}",
                    "Content-Type": "application/json;",
                },
            }
            err = RequestDataError(
                f"{action.upper()} method must contain object id"
                ' in the {"id": 1} format',
                action,
            )
            if action in ("patch", "put", "post"):
                params = {"json": kwargs[action], **params}
        if "{id}" in endpoint:
            try:
                id_ = f"{kwargs[action]['id']}"
                endpoint = re.sub(r"{id}", id_, endpoint)
            except (KeyError, TypeError):
                raise err

        req = await getattr(self.api.http_session, action)(
            f"{self.api.base_url}{endpoint}",
            **params,
        )
        return req

    async def request(self, kwargs: Dict[str, Any]) -> E:
        """Send http request

        Args:
            kwargs: dict with http request action + params/data.
                kwargs example: {"get": {"name": "some_name"}}

        Returns:
            EndpointIdIterator or EndpointId class object.

            EndpointIdIterator class object: If httpx.Response.json()
                contains many results. EndpointIdIterator is Iterator
                with EndpointId objects.
            EndpointId class object: If httpx.Response.json()
                contains a single result.
                EndpointId describes NetBox object (site, device, circuit, etc.)

        Raises:
            httpx._exceptions:
                See https://github.com/encode/httpx/blob/master/httpx/_exceptions.py
            RequestDataError: For invalid http request data
            RequestParamsError: For invalid http request params
            The difference between data and parameters - https://www.python-httpx.org/quickstart/
        """
        req = await self._request(kwargs)

        if req.status_code == 204 and "post" in kwargs:
            raise httpx.RequestError("Request allocation error")

        raise_for_status(req)

        return await EndpointIdIterator(
            api=self.api, url=self.url, endpoint=self.endpoint, response=req
        )()


class ValidateEndpoint(BaseModel):
    kwargs: KwargsType

    @validator("kwargs", pre=True, always=True)
    def set_default_kwargs(cls, v: KwargsType) -> KwargsType:
        return v or {"get": {}}

    @validator("kwargs")
    def check_requests(cls, v: KwargsType) -> KwargsType:
        for key in v:
            if key not in ("get", "put", "post", "patch", "delete"):
                raise ValueError(
                    "Available arguments: "
                    "'get', 'put', 'post', 'patch', 'delete'"
                )
        return v


@dataclasses.dataclass
class EndpointAsIterator(EndpointBase):
    kwargs: KwargsType = dataclasses.field(repr=False)

    def __post_init__(self) -> None:
        self.model = self.dict_generator(self.kwargs)

    def __iter__(self) -> "EndpointAsIterator":
        return self

    def __next__(self) -> Coroutine[Any, Any, E]:
        model = next(self.model)
        return self.request(model)

    @staticmethod
    def dict_generator(
        kwargs: KwargsType,
    ) -> Iterator[KwargsType]:
        for t in [*kwargs.items()]:
            d = dict([t])
            value = [*d.values()][0]
            if value:
                if isinstance(value, list):
                    for item in zip_longest(
                        d, *d.values(), fillvalue="".join(d)
                    ):
                        yield dict([item])
                else:
                    yield d
            else:
                yield {[*d][0]: {}}


@dataclasses.dataclass
class Endpoint(EndpointBase):
    """NetBox API endpoint object
    ('/dcim/devices', '/ipam/roles', ...)

    Args:
        api (anac.core.Api): Api class object
        url (str): NetBox url
        endpoint (str): NetBox API endpoint str ('/dcim/devices/', ...)

    What is Endpoint:
        In [1]: from anac import api
           ...:
           ...: a = api(
           ...:     "http://netbox/",
           ...:     token="api_token",
           ...: )
           ...: await a.openapi()

        In [2]: type(a.dcim_devices)
        Out[2]: anac.core.endpoint.Endpoint

        In [3]: type(a.circuits_circuits)
        Out[3]: anac.core.endpoint.Endpoint
    """

    async def __call__(
        self, **kwargs: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> Union[E, "EndpointAsIterator"]:
        """Endpoint object is a coroutine
        for interacting with NetBox API endpoint.

                                                 EndpointIdAsIterator
                                                 /
                    EndpointIdIterator/EndpointId
                    /                            \
        Api-Endpoint                             EndpointId
                    \
                    EndpointAsIterator

        You can run each Endpoint object:
        - to send http request and get results
        - to get Iterator with EndpointBase.request coroutines for pending http requests
        and running in event loop with asyncio.gather or asyncio.as_completed

        Args:
            kwargs: list or dict with http request actions + params/data

        Returns:
            - EndpointId class object: Describes NetBox object (site, device, circuit,
                etc.)
            - EndpointIdIterator class object: Iterator with EndpointId objects
            - EndpointAsIterator class object: Iterator with EndpointBase.request
                coroutines for pending http requests and running in event loop
                with asyncio.gather or asyncio.as_completed

            This coroutine has simple logic and returns:
                - EndpointId or EndpointIdIterator if kwargs is a dict
                - EndpointAsIterator if kwargs is a list

        Raises:
            httpx._exceptions:
                See https://github.com/encode/httpx/blob/master/httpx/_exceptions.py
            RequestDataError: For invalid http request data
            RequestParamsError: For invalid http request params
            The difference between data and parameters -
            https://www.python-httpx.org/quickstart/

        Usage:
            - get 'test_device' NetBox '/dcim/devices/' object as EndpointId class
            object:
            In [1]: from anac import api
               ...:
               ...: a = api(
               ...:     "http://netbox/",
               ...:     token="token",
               ...: )
               ...: await a.openapi()

            In [2]: test_device = await a.dcim_devices(get={"name": "test"})

            In [3]: test_device
            Out[3]: EndpointId(api=Api, url='http://netbox/api',
            endpoint='/dcim/devices/')

            In [4]: test_device.name
            Out[4]: 'test'

            In [5]: test_device.id
            Out[5]: 4010

            In [6]: test_device.device_role
            Out[6]:
            {'id': 1,
             'url': 'http://netbox/api/dcim/device-roles/1/',
             'name': 'TEST',
             'slug': 'test'}

            In [7]: test_device.device_role.id
            Out[7]: 1

            - get NetBox '/dcim/devices/' objects with 'manufacturer id' = 1 as
            EndpointIdIterator class object:
                In [8]: test_devices = await a.dcim_devices(
                    ...:     get={"device_type": {"manufacturer": {"id": 1}},
                                  "limit": 2}
                    ...: )

                In [9]: len(test_devices)
                Out[9]: 2

                In [10]: for test_device in test_devices:
                    ...:     print(test_device.id)
                4010
                3988

                In [11]: test_devices[0]
                Out[11]: EndpointId(api=Api, url='http://netbox/api',
                endpoint='/dcim/devices/')

                In [12]: test_devices[1]
                Out[12]: EndpointId(api=Api, url='http://netbox/api',
                endpoint='/dcim/devices/')

                In [13]: test_devices[0].name
                Out[13]: 'test'

                In [14]: test_devices[1].name
                Out[14]: 'test1'

            - post 2 new NetBox '/dcim/devices/' objects with EndpointAsIterator class
            object:
                In [23]: pending_new_devices = await a.dcim_devices(
                    ...:     post=[
                    ...:         {"name": "test2", "device_role": 1, "site": 1,
                                  "device_type": 1, "status": 1},
                    ...:         {"name": "test3", "device_role": 1, "site": 1,
                                  "device_type": 1, "status": 1},
                    ...:     ]
                    ...: )

                In [24]: pending_new_devices
                Out[24]: EndpointAsIterator(api=Api, url='http://netbox/api',
                endpoint='/dcim/devices/')

                In [25]: import asyncio

                In [26]: new_devices = await asyncio.gather(*pending_new_devices)

                In [27]: new_devices
                Out[27]:
                [EndpointId(api=Api, url='http://netbox/api',
                endpoint='/dcim/devices/'),
                 EndpointId(api=Api, url='http://netbox/api',
                 endpoint='/dcim/devices/')]

                In [28]: for new_device in new_devices:
                    ...:     print(new_device.id)
                4074
                4075

                In [29]: new_devices[0]
                Out[29]: EndpointId(api=Api, url='http://netbox/api',
                endpoint='/dcim/devices/')

                In [30]: new_devices[0].name
                Out[30]: 'test2'

                In [31]: new_devices[1]
                Out[31]: EndpointId(api=Api, url='http://netbox/api',
                endpoint='/dcim/devices/')

                In [32]: new_devices[1].name
                Out[32]: 'test3'
        """
        kwargs = ValidateEndpoint(kwargs=kwargs).kwargs

        if len(kwargs) == 1 and isinstance([*kwargs.values()][0], dict):
            req = await self.request(kwargs)
        else:
            return EndpointAsIterator(
                api=self.api,
                url=self.url,
                endpoint=self.endpoint,
                kwargs=kwargs,
            )
        return req


class ValidateEndpointId(BaseModel):
    kwargs: KwargsDict

    @validator("kwargs", pre=True, always=True)
    def set_default_kwargs(cls, v: KwargsDict) -> KwargsDict:
        return v or {"get": {}}

    @validator("kwargs")
    def check_requests(cls, v: KwargsDict) -> KwargsDict:
        for key in v:
            if key not in ("get", "put", "patch", "delete"):
                raise ValueError(
                    "Available arguments: 'get', 'put', 'patch', 'delete'"
                )
        return v


class DictAttribute(dict):
    pass


@dataclasses.dataclass
class EndpointIdAsIterator:
    """Iterator with EndpointId objects

    EndpointIdAsIterator contains the results of modifying a single
    NetBox object (with endpoint id), using the EndpointId coroutine,
    running with multiple arguments. These results are iterated
    according to the order of the EndpointId arguments (see example below).

    Args:
        responses: EndpointId objects list

    What is EndpointIdAsIterator:
        In [1]: from anac import api
           ...:
           ...: a = api(
           ...:     "http://netbox/",
           ...:     token="api_token",
           ...: )
           ...: await a.openapi()

        In [2]: test_device = await a.dcim_devices(get={"name": "test"})

        In [3]: test_device
        Out[3]: EndpointId(api=Api, url='http://netbox/api', endpoint='/dcim/devices/')

        In [4]: test_device.name
        Out[4]: test

        In [5]: test_device = await test_device(
            ...:     put={
            ...:         "name": "supertest",
            ...:         "device_role": 2,
            ...:         "site": 2,
            ...:         "device_type": 2,
            ...:         "status": 2,
            ...:     },
            ...:     patch={"name": "megatest"},
            ...: )

        In [6]: test_device
        Out[6]: EndpointIdAsIterator()

        In [7]: list(test_device)
        Out[7]:
        [EndpointId(api=Api, url='http://netbox/api', endpoint='/dcim/devices/{id}/'),
         EndpointId(api=Api, url='http://netbox/api', endpoint='/dcim/devices/{id}/')]

        In [8]: test_device[0].name
        Out[8]: 'supertest'

        In [9]: test_device[1].name
        Out[9]: 'megatest'
    """
    responses: List[Any] = dataclasses.field(repr=False)

    def __post_init__(self) -> None:
        self._index = 0

    def __iter__(self) -> "EndpointIdAsIterator":
        return self

    def __getitem__(self, index: int) -> "EndpointId":
        return self.responses[index]

    def __next__(self) -> "EndpointId":
        if self._index >= len(self.responses):
            raise StopIteration
        response = self.responses[self._index]
        self._index += 1
        return response

    def __len__(self) -> int:
        return len(self.responses)


@dataclasses.dataclass
class EndpointId(EndpointBase):
    """NetBox API endpoint id object
    ('/dcim/devices/{id}', '/ipam/roles/{id}', ...).

    EndpointId object has all attributes of NetBox object.
    EndpointId object has .response attribute, containing httpx.Response object.

    Args:
        api (anac.core.Api): Api class object
        url (str): NetBox url
        endpoint (str): NetBox API endpoint str ('/dcim/devices/', ...)

    What is EndpointId:
        In [1]: from anac import api
           ...:
           ...: a = api(
           ...:     "http://netbox/",
           ...:     token="api_token",
           ...: )
           ...: await a.openapi()

        In [2]: test_device = await a.dcim_devices(get={"name": "test"})

        In [3]: type(test_device)
        Out[3]: anac.core.endpoint.EndpointId

        In [4]: test_device.id
        Out[4]: 4010
    """
    kwargs: Dict[str, Any] = dataclasses.field(repr=False)

    def __post_init__(self) -> None:
        self.generate_attrs(self, self.kwargs)

    def generate_attrs(self, obj: T, dict_: Dict[str, Any]) -> None:
        for key, value in dict_.items():
            if isinstance(value, dict):
                dict_obj = DictAttribute(value)
                setattr(obj, key.lower().replace(" ", "_"), dict_obj)
                self.generate_attrs(dict_obj, value)
            else:
                setattr(
                    obj,
                    key.lower().replace(" ", "_"),
                    value,
                )

    def __str__(self):
        return self.__class__.__name__

    def __getattr__(self, name: str) -> Any:
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError(
                f"'{str(self)}' object has no attribute '{name}'"
            )

    async def __call__(
        self, **kwargs: Dict[str, Any]
    ) -> Union[E, "EndpointIdAsIterator"]:
        """EndpointId object is a coroutine
        for interacting with NetBox API endpoint id.

        You can run each EndpointId object:
        - to send http request and get results/new EndpointId objects
        - to send http requests and get Iterator with results/new EndpointId objects.
            All http requests in this coroutine will be run serially using 'await'.

                                                 EndpointIdAsIterator
                                                 /
                    EndpointIdIterator/EndpointId
                    /                            \
        Api-Endpoint                             EndpointId
                    \
                    EndpointAsIterator

        Args:
            kwargs: dict with http request actions + params/data

        Returns:
            - new EndpointId class object: Describes NetBox object (site, device,
                circuit, etc.)
            - EndpointIdAsIterator class object: Iterator with new EndpointId objects

        Raises:
            httpx._exceptions:
                See https://github.com/encode/httpx/blob/master/httpx/_exceptions.py
            RequestDataError: For invalid http request data
            RequestParamsError: For invalid http request params
            The difference between data and parameters -
            https://www.python-httpx.org/quickstart/

        Usage:
            In [1]: from anac import api
               ...:
               ...: a = api(
               ...:     "http://netbox/",
               ...:     token="api_token",
               ...: )
               ...: await a.openapi()

            In [2]: test_device = await a.dcim_devices(get={"name": "test"})

            In [3]: type(test_device)
            Out[3]: anac.core.endpoint.EndpointId

            In [4]: test_device.name
            Out[4]: test

            In [5]: test_device = await test_device(get={}, patch={"name": "testtest"})

            In [6]: test_device
            Out[6]: EndpointIdAsIterator()

            In [7]: list(test_device)
            Out[7]:
            [EndpointId(api=Api, url='http://netbox/api', endpoint='/dcim/devices/{id}/'),
             EndpointId(api=Api, url='http://netbox/api', endpoint='/dcim/devices/{id}/')]

            In [8]: test_device[0].name
            Out[8]: 'test'

            In [9]: test_device[1].name
            Out[9]: 'testtest'
        """
        self.endpoint = (
            f"{self.endpoint}"
            if "{id}" in self.endpoint
            else f"{self.endpoint}{'{id}/'}"
        )

        kwargs = ValidateEndpointId(kwargs=kwargs).kwargs

        new_kwargs: KwargsType = {
            key: {"id": self.id, **value} for key, value in kwargs.items()
        }

        if len(new_kwargs) == 1:
            return await self.request(new_kwargs)
        else:
            responses = []
            models = EndpointAsIterator.dict_generator(new_kwargs)
            for model in models:
                responses.append(await self.request(model))
            return EndpointIdAsIterator(
                responses=responses,
            )


@dataclasses.dataclass
class EndpointIdIterator:
    """Iterator with EndpointId objects

    EndpointIdIterator contains the multiple EndpointId objects,
    if Endpoint http request returns more than one result
    (httpx.Response.json()['results'])

    Args:
        api (anac.core.Api): Api class object
        url (str): NetBox url
        endpoint (str): NetBox API endpoint str ('/dcim/devices/', ...)
        response (httpx.Response): httpx.Response object

    What is EndpointIdIterator:
        In [1]: from anac import api
           ...:
           ...: a = api(
           ...:     "http://netbox/",
           ...:     token="api_token",
           ...: )
           ...: await a.openapi()

        In [2]: all_devices = await a.dcim_devices(get={"limit": 100})

        In [3]: all_devices
        Out[3]: EndpointIdIterator(api=Api, url='http://netbox/api',
        endpoint='/dcim/devices/')

        In [4]: len(all_devices)
        Out[4]: 100
    """
    api: "Api"
    url: str
    endpoint: str
    response: httpx.Response = dataclasses.field(repr=False)

    def __post_init__(self) -> None:
        self._index: int = 0
        self._responses: List[EndpointId] = []
        self.dict_data: Dict[str, Any] = {}
        self.list_data: List[Dict[str, Any]] = []

        httpx_models_response = {"response": self.response}
        try:
            self.list_data = self.response.json()["results"]
            if len(self.list_data) == 1:
                self.dict_data = {**httpx_models_response, **self.list_data[0]}
        except KeyError:
            self.dict_data = {**httpx_models_response, **self.response.json()}
        except JSONDecodeError:
            if self.response.request.method == "DELETE":
                self.dict_data = httpx_models_response
            else:
                raise httpx.DecodingError("The server returned non json data")

    async def __call__(self) -> E:
        """EndpointIdIterator object is a service coroutine
        for using with EndpointBase.request coroutine

                                                 EndpointIdAsIterator
                                                 /
                    EndpointIdIterator/EndpointId
                    /                            \
        Api-Endpoint                             EndpointId
                    \
                    EndpointAsIterator

        Returns:
            - EndpointId class object: Describes NetBox object (site, device, circuit,
                etc.)
            - EndpointIdIterator class object: Iterator with multiple EndpointId objects

        Raises:
            N/A
        """
        if self.dict_data:
            return EndpointId(
                api=self.api,
                url=self.url,
                endpoint=self.endpoint,
                kwargs=self.dict_data,
            )
        self._responses = [
            EndpointId(
                api=self.api, url=self.url, endpoint=self.endpoint, kwargs=data
            )
            for data in self.list_data
        ]
        return self

    def __iter__(self) -> "EndpointIdIterator":
        return self

    def __getitem__(self, index: int) -> "EndpointId":
        return self._responses[index]

    def __next__(self) -> "EndpointId":
        if self._index >= len(self._responses):
            raise StopIteration
        response = self._responses[self._index]
        self._index += 1
        return response

    def __len__(self) -> int:
        return len(self._responses)
