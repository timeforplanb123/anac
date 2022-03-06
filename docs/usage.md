## Api

At first, get `Api` object and run `openapi` coroutine

```python
from anac import api

a = api(
    "https://demo.netbox.dev",
    token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
)
# get openapi spec and create attributes/endpoints
# with python interpreter autocompletion
await a.openapi()
```

!!! tip
    Use [IPython](https://ipython.readthedocs.io/en/stable/) or Python 3.8+ with `python -m asyncio` to try this code interactively, as they support executing `async`/`await` expressions in the console.


## Endpoint*

The fundamental anac principle is a minimalistic user interface.

anac provides 5 `Endpoint*` classes, whose objects are a coroutine or coroutine iterators, for interacting with the NetBox API endpoints.

Here is the diagram with these objects/coroutines:
```text
                                         EndpointIdAsIterator
                                         /
            EndpointIdIterator/EndpointId
            /                            \
Api-Endpoint                             EndpointId
            \
            EndpointAsIterator
```
For example, basic `Endpoint` object is coroutine, that can return `EndpointIdIterator`/`EndpointId` or `EndpointAsIterator` objects, where `*Iterator` are coroutine iterators, and not `*Iterator` is a coroutine. 


#### Endpoint

```python
# use 'tab' autocompletion
In [1]: a.dcim_devices
Out[1]: Endpoint(api=Api, url='https://demo.netbox.dev/api',
endpoint='/dcim/devices/')

In [2]: type(a.dcim_devices)
Out[2]: anac.core.endpoint.Endpoint

In [3]: a.circuits_circuits
Out[3]: Endpoint(api=Api, url='https://demo.netbox.dev/api',
endpoint='/circuits/circuits/')

In [4]: type(a.circuits_circuits)
Out[4]: anac.core.endpoint.Endpoint

In [5]: a.dcim_cables_id
Out[5]: Endpoint(api=Api, url='https://demo.netbox.dev/api',
endpoint='/dcim/cables/{id}/')

In [6]: type(a.dcim_cables_id)
Out[6]: anac.core.endpoint.Endpoint
```

`Endpoint` describes NetBox API endpoint object (`'/dcim/devices'`, `'/ipam/roles'`, ...) and, at the same time, it's a coroutine for interacting with NetBox API endpoint.

You can run each `Endpoint` coroutine with:

- dict argument to send http request and get result as `EndpointId` or `EndpointIdIterator` object
    ```python
    In [7]: some_device = await a.dcim_devices(get={"name": "dmi01-scranton-rtr01"})

    In [8]: some_device
    Out[8]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/9/',
    endpoint='/dcim/devices/')
    ```

    To continue working with `EndpointId` see [`EndpointId`](#endpointid)

    ```python
    # by default, you get 50 results,
    # but you can specify the required number with 'get={"limit": 100}'
    In [9]: all_devices = await a.dcim_devices(get={})
    # or
    In [10]: all_devices = await a.dcim_devices()

    In [11]: all_devices
    Out[11]: EndpointIdIterator(api=Api, url='https://demo.netbox.dev/api',
    endpoint='/dcim/devices/')
    ```

    To continue working with `EndpointIdIterator` see [`EndpointIdIterator`](#endpointiditerator)

- list of dicts arguments to get coroutine iterator as `EndpointAsIterator` object for pending http requests and running them in event loop with asyncio
    ```python
    In [12]: devices = await a.dcim_devices(
    ...:     get=[
    ...:         {"name": "dmi01-scranton-rtr01"},
    ...:         {"name": "dmi01-scranton-sw01"},
    ...:     ],
    ...:     post=[
    ...:         {
    ...:             "name": "dmi01-scranton-rtr02",
    ...:             "device_role": 1,
    ...:             "site": 10,
    ...:             "device_type": 6,
    ...:             "status": "planned",
    ...:         },
    ...:         {
    ...:             "name": "dmi01-scranton-sw02",
    ...:             "device_role": 1,
    ...:             "site": 10,
    ...:             "device_type": 7,
    ...:             "status": "planned",
    ...:         },
    ...:     ],
    ...: )

    In [13]: devices
    Out[13]: EndpointAsIterator(api=Api, url='https://demo.netbox.dev/api',
    endpoint='/dcim/devices/')
    ```

    To continue working with `EndpointAsIterator` see [`EndpointAsIterator`](#endpointasiterator)


#### EndpointId

`EndpointId` describes NetBox API endpoint id object (`'/dcim/devices/{id}'`, `'/ipam/roles/{id}'`, ...) and, at the same time, it's a coroutine for interacting with NetBox API endpoint id.

`EndpointId` object has all attributes of NetBox object.
`EndpointId` object has `.response` attribute, containing `httpx.Response` object.

Where does `some_device` from? See [`Endpoint`](#endpoint)

```python
# we sent 1 http request earlier:
# some_device = await a.dcim_devices(get={"name": "dmi01-scranton-rtr01"})
In [14]: some_device
Out[14]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/9/',
endpoint='/dcim/devices/')

# use 'tab' autocompletion
In [15]: some_device.id
Out[15]: 9

In [16]: some_device.name
Out[16]: 'dmi01-scranton-rtr01'

In [17]: some_device.device_type.model
Out[17]: 'ISR 1111-8P'

In [18]: some_device.response.json()
Out[18]: 
{'count': 1,
 'next': None,
 'previous': None,
 'results': [{'id': 9,
   'url': 'https://demo.netbox.dev/api/dcim/devices/9/',
   'display': 'dmi01-scranton-rtr01',
   'name': 'dmi01-scranton-rtr01',
   'device_type': {'id': 6,
    'url': 'https://demo.netbox.dev/api/dcim/device-types/6/',
    'display': 'ISR 1111-8P',
    'manufacturer': {'id': 3,
     'url': 'https://demo.netbox.dev/api/dcim/manufacturers/3/',
     'display': 'Cisco',
     'name': 'Cisco',
     'slug': 'cisco'},
    'model': 'ISR 1111-8P',
    'slug': 'isr1111'},
   'device_role': {'id': 1,
...
```

You can run each `EndpointId` object:

- to send http request and get results/new `EndpointId` object
    ```python
    In [19]: some_device = await some_device(patch={"status": "planned"})

    # some_device is a new 'EndpointId' object
    In [20]: some_device
    Out[20]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/9/',
    endpoint='/dcim/devices/{id}/')

    In [21]: some_device.status
    Out[21]: {'value': 'planned', 'label': 'Planned'}
    ```
- to send http requests and get `EndpointIdAsIterator` with results/new `EndpointId` objects. All http requests in this coroutine will be run serially using `await`.
    ```python
    In [22]: some_devices = await some_device(get={}, patch={"status": "active"})

    In [23]: some_devices
    Out[23]: EndpointIdAsIterator()
    ```

    To continue working with `EndpointIdAsIterator` see [`EndpointIdAsIterator`](#endpointidasiterator)


#### EndpointIdIterator

`EndpointIdIterator` is an iterator with [`EndpointId`](#endpointid) objects.

`EndpointIdIterator` contains the multiple `EndpointId` objects, if `Endpoint` http
request returns more than one result (`httpx.Response.json()['results']`) and, at the
same time, `EndpointIdIterator` object is a service coroutine for using with service `EndpointBase.request` coroutine

Where does `all_devices` from? See [`Endpoint`](#endpoint)
```python
# we sent 1 http request earlier:
# all_devices = await a.dcim_devices(get={})
In [31]: all_devices
Out[31]: EndpointIdIterator(api=Api, url='https://demo.netbox.dev/api',
endpoint='/dcim/devices/')

In [32]: list(all_devices)
Out[32]:
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/107/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/88/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/89/',
 endpoint='/dcim/devices/'),
...]

In [33]: all_devices[0].name
Out[33]: 'Dingdong'

In [34]: all_devices[49].name
Out[34]: 'ncsu118-distswitch1'

In [35]: len(all_devices)
Out[35]: 50
```


#### EndpointAsIterator

`EndpointAsIterator` is an iterator with `EndpointBase.request` (it's service http
request coroutine) coroutines for pending http requests and running in event loop with `asyncio.gather` or `asyncio.as_completed`.


Where does `devices` from? See [`Endpoint`](#endpoint)
```python
# we planned to send 4 http requests earlier:
# devices = await a.dcim_devices(
#     get=[
#         {"name": "dmi01-scranton-rtr01"},
#         {"name": "dmi01-scranton-sw01"},
#     ],
#     post=[
#         {
#             "name": "dmi01-scranton-rtr02",
#             "device_role": 1,
#             "site": 10,
#             "device_type": 6,
#             "status": "planned",
#         },
#         {
#             "name": "dmi01-scranton-sw02",
#             "device_role": 1,
#             "site": 10,
#             "device_type": 7,
#             "status": "planned",
#         },
#     ],
# )
In [36]: devices
Out[36]: EndpointAsIterator(api=Api, url='https://demo.netbox.dev/api',
endpoint='/dcim/devices/')

In [37]: import asyncio

In [38]: devices = await asyncio.gather(*some_devices)

In [39]: devices
Out[39]: 
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/9/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/22/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/115/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/114/',
 endpoint='/dcim/devices/')]
```


#### EndpointIdAsIterator

`EndpointIdAsIterator` is an iterator with [`EndpointId`](#endpointid) objects.

`EndpointIdAsIterator` contains the results of modifying a single NetBox object (with endpoint id), using the `EndpointId` coroutine, running with multiple arguments. 
These results are iterated according to the order of the `EndpointId` arguments (see example below).

Where does `some_devices` from? See [`EndpointId`](#endpointid)

```python
# we sent 2 http requests earlier:
# some_devices = await some_devices(get={}, patch={"status": "active"})
In [24]: some_devices
Out[24]: EndpointIdAsIterator()

In [25]: list(some_devices)
Out[25]:
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/9/',
 endpoint='/dcim/devices/{id}/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/9/',
 endpoint='/dcim/devices/{id}/')]

# 'get={}' results
In [26]: some_devices[0].name
Out[26]: 'dmi01-scranton-rtr01'

In [27]: some_devices[0].status
Out[27]: {'value': 'planned', 'label': 'Planned'}

# 'patch={"status": "active"}' results
In [28]: some_devices[1].name
Out[28]: 'dmi01-scranton-rtr01'

In [29]: some_devices[1].status
Out[29]: {'value': 'active', 'label': 'Active'}

In [30]: len(some_devices)
Out[30]: 2
```


## Examples

At first, get `Api` object and run `openapi` coroutine(btw, it works with async context
manager)
```python
from anac import api

a = api(
    "https://demo.netbox.dev",
    token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
)
# get openapi spec and create attributes/endpoints   
await a.openapi()
```
and then:


#### `get` some device and `patch` it 
```python
In [1]: some_device = await a.dcim_devices(get={"name": "dmi01-rochster-sw01"})

In [2]: some_device.name
Out[2]: 'dmi01-rochster-sw01'

In [3]: some_device.status
Out[3]: {'value': 'active', 'label': 'Active'}

In [5]: some_device = await some_device(patch={"status": "failed"})

In [6]: some_device.status
Out[6]: {'value': 'failed', 'label': 'Failed'}
```


#### `get` some 2 devices and `put` + `patch` them
```python
In [7]: some_devices = await a.dcim_devices(
    ...:     get=[
    ...:        {"name": "dmi01-rochster-sw01"},
    ...:        {"name": "dmi01-rochester-rtr01"},
    ...:     ]
    ...: )

# EndpointAsIterator is a coroutine iterator with 2 coroutines
In [8]: some_devices
Out[8]: EndpointAsIterator(api=Api, url='https://demo.netbox.dev/api',
endpoint='/dcim/devices/')

In [9]: import asyncio

# run 2 coroutines in the event loop
In [10]: some_devices = await asyncio.gather(*some_devices)

# EndpointId is a NetBox '/dcim/devices/' object and coroutine
In [11]: some_devices
Out[11]: 
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/21/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/8/',
 endpoint='/dcim/devices/')]

In [12]: patch_some_devices = [coro(patch={"status": "failed"}) for coro in some_devices]

# run 2 coroutines in the event loop
In [13]: patch_some_devices = await asyncio.gather(*patch_some_devices)

# EndpointId is a coroutine, again
In [14]: patch_some_devices
Out[14]: 
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/21/',
 endpoint='/dcim/devices/{id}/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/8/',
 endpoint='/dcim/devices/{id}/')]

In [15]: patch_some_devices[0].name
Out[15]: 'dmi01-rochster-sw01'

In [16]: patch_some_devices[0].status
Out[16]: {'value': 'failed', 'label': 'Failed'}

In [17]: patch_some_devices[1].name
Out[17]: 'dmi01-rochester-rtr01'

In [18]: patch_some_devices[1].status
Out[18]: {'value': 'failed', 'label': 'Failed'}
```


#### `get` all devices
```python
In [19]: all_devices = await a.dcim_devices(get={})
# or
In [20]: all_devices = await a.dcim_devices()

# EndpointIdIterator is an coroutine iterator with EndpointId objects
In [21]: all_devices
Out[21]: EndpointIdIterator(api=Api, url='https://demo.netbox.dev/api',
endpoint='/dcim/devices/')

In [22]: len(all_devices)
Out[22]: 50

In [23]: all_devices[49]
Out[23]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/95/',
endpoint='/dcim/devices/')

In [24]: all_devices[49].name
Out[24]: 'ncsu118-distswitch1'

# by default, 'limit' parameter = 50,
# but you can run 'get' request with custom 'limit'
In [25]: all_devices = await a.dcim_devices(get={"limit": 100})

In [26]: len(all_devices)
Out[26]: 75

In [27]: all_devices[74]
Out[27]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/106/',
endpoint='/dcim/devices/')

In [28]: all_devices[74].id
Out[28]: 106
```

#### `get` all devices and `post` 2 new devices
```python
In [29]: all_test = await a.dcim_devices(
    ...:     get={},
    ...:     post=[
    ...:         {
    ...:             "name": "test1",
    ...:             "device_role": 1,
    ...:             "site": 1,
    ...:             "device_type": 1,
    ...:             "status": "planned",
    ...:         },
    ...:         {
    ...:             "name": "test2",
    ...:             "device_role": 1,
    ...:             "site": 1,
    ...:             "device_type": 1,
    ...:             "status": "planned",
    ...:         },
    ...:     ],
    ...: )

# run 3 coroutines in the event loop
In [30]: all_test = await asyncio.gather(*all_test)

# EndpointIdIterator is an coroutine iterator with EndpointId objects
# EndpointId is a NetBox '/dcim/devices/' object and coroutine
In [31]: all_test
Out[31]: 
[EndpointIdIterator(api=Api, url='https://demo.netbox.dev/api',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/110/',
 endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/111/',
 endpoint='/dcim/devices/')]

In [32]: all_test[0][49].name
Out[32]: 'ncsu118-distswitch1'

In [33]: all_test[1].name
Out[34]: 'test1'

In [35]: all_test[2].name
Out[35]: 'test2'

# httpx.Response is available with .response attribute
In [36]: all_test[1].response.json()
Out[36]:
{'id': 110,
 'url': 'https://demo.netbox.dev/api/dcim/devices/110/',
 'display': 'test1',
 'name': 'test1',
 'device_type': {'id': 1,
  'url': 'https://demo.netbox.dev/api/dcim/device-types/1/',
  'display': 'MX480',
  'manufacturer': {'id': 7,
  ...
}
```
#### `post` or `put` using a `name` instead of an `id`

It is not always convenient to send a `post` or `put` http request, using only object `id`s. 

You can use `name`s or other keys. For example:
```python
In [37]: test3_device = await a.dcim_devices(
     ...:     post={
     ...:         "name": "test3",
     ...:         "device_role": {"name": "Access Switch"},
     ...:         "site": {"name": "DM-Rochester"},
     ...:         "device_type": {"model": "C9200-48P"},
     ...:         "status": "planned",
     ...:     }
     ...: )

In [38]: test3_device.name
Out[38]: 'test3'

In [39]: test3_device.device_role.name
Out[39]: 'Access Switch'

In [40]: test3_device.site.name
Out[40]: 'DM-Rochester'

In [41]: test3_device.device_type.model
Out[41]: 'C9200-48P'
```

Or you can write a coroutine, that will search the `id` by key:

```python
In [42]: from typing import Dict, Any
    ...:
    ...:
    ...: async def finder(endpoint: "Endpoint", kwargs: Dict[str, Any]):
    ...:     endpoint_id = await endpoint(get=kwargs)
    ...:     return endpoint_id.id

In [43]: d = {
    ...:     "device_role": (a.dcim_device_roles, {"name": "Access Switch"}),
    ...:     "site": (a.dcim_sites, {"name": "DM-Rochester"}),
    ...:     "device_type": (a.dcim_device_types, {"model": "C9200-48P"}),
    ...: }

In [44]: coros = [finder(*v) for v in d.values()]

In [45]: ids = await asyncio.gather(*coros)

In [46]: ids
Out[46]: [4, 9, 7]

In [47]: d = {"name": "test3", "status": "planned", **dict(zip(d, ids))}

In [48]: d
Out[48]:
{'name': 'test3',
 'status': 'planned',
 'device_role': 4,
 'site': 9,
 'device_type': 7}

In [49]: test3_device = await a.dcim_devices(post=d)

In [50]: test3_device.device_role.name
Out[50]: 'Access Switch'

In [51]: test3_device.site.name
Out[51]: 'DM-Rochester'

In [52]: test3_device.device_type.model
Out[52]: 'C9200-48P'
```
