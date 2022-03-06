[![Code style: black](https://img.shields.io/badge/code%20style-black-black?style=for-the-badge)](https://github.com/ambv/black)
[![PyPI](https://img.shields.io/pypi/v/anac?style=for-the-badge)](https://pypi.org/project/anac)
[![License: APACHE-2.0](https://img.shields.io/github/license/timeforplanb123/anac?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Docs](https://img.shields.io/badge/docs-passing-green?style=for-the-badge)](https://timeforplanb123.github.io/anac/)

anac
==========

Python **A**sync **N**etBox **A**PI **C**lient, based on <a href="https://github.com/encode/httpx" target="_blank">httpx</a> and <a href="https://github.com/samuelcolvin/pydantic" target="_blank">pydantic</a>


## Documentation

<a href="https://timeforplanb123.github.io/anac" target="_blank">https://timeforplanb123.github.io/anac</a>


## Features 

* Minimalistic interface
* Async only
* Python interpreter autocompletion
* Supports <a href="https://github.com/netbox-community/netbox" target="_blank">NetBox</a> 2.x, 3.x
* Flexibility. All the objects are coroutines or coroutine iterators
* Simple integration with parsers (<a href="https://github.com/google/textfsm" target="_blank">TextFSM</a>, <a href="https://github.com/dmulyalin/ttp" target="_blank">TTP</a>)


## Quick Start 

#### Install

Please, at first, check the dependencies in `pyproject.toml` and create new virtual environment if necessary and then:

**with pip:**

```text
pip install anac 
```

**with git:**

```text
git clone https://github.com/timeforplanb123/anac.git
cd anac 
pip install .
# or
poetry install
```


#### Simple Examples


#### Api Instantiating
```python
from anac import api

a = api(
    "https://demo.netbox.dev",
    token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
)
# get openapi spec and create attributes/endpoints   
await a.openapi()
```
#### `get` some device and `patch` it 

[![asciicast](https://asciinema.org/a/DmirYBxwl40VP9Delp6e0J3dE.svg)](https://asciinema.org/a/DmirYBxwl40VP9Delp6e0J3dE)

```python
In [1]: some_device = await a.dcim_devices(get={"name": "dmi01-rochster-sw01"})

In [2]: some_device.name
Out[2]: 'dmi01-rochster-sw01'

In [3]: some_device.device_type
Out[3]:
{'id': 7,
 'url': 'https://demo.netbox.dev/api/dcim/device-types/7/',
 'display': 'C9200-48P',
 'manufacturer': {'id': 3,
  'url': 'https://demo.netbox.dev/api/dcim/manufacturers/3/',
  'display': 'Cisco',
  'name': 'Cisco',
  'slug': 'cisco'},
 'model': 'C9200-48P',
 'slug': 'c9200-48p'}

In [4]: some_device.status
Out[4]: {'value': 'active', 'label': 'Active'}

In [5]: some_device = await some_device(patch={"status": "failed"})

In [6]: some_device.status
Out[6]: {'value': 'failed', 'label': 'Failed'}
```

#### `get` some 2 devices and `put` + `patch` them
```python
In [7]: some_devices = await a.dcim_devices(
    ...:     get=[{"name": "dmi01-rochster-sw01"}, {"name": "dmi01-rochester-rtr01"}]
    ...: )

# EndpointAsIterator is a coroutine iterator with 2 coroutines
In [8]: some_devices
Out[8]: EndpointAsIterator(api=Api, url='https://demo.netbox.dev/api', endpoint='/dcim/devices/')

In [9]: import asyncio

# run 2 coroutines in the event loop
In [10]: some_devices = await asyncio.gather(*some_devices)

# EndpointId is a NetBox '/dcim/devices/' object and coroutine
In [11]: some_devices
Out[11]: 
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/21/', endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/8/', endpoint='/dcim/devices/')]

In [12]: patch_some_devices = [coro(patch={"status": "failed"}) for coro in some_devices]

# run 2 coroutines in the event loop
In [13]: patch_some_devices = await asyncio.gather(*patch_some_devices)

# EndpointId is a coroutine, again
In [14]: patch_some_devices
Out[14]: 
[EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/21/', endpoint='/dcim/devices/{id}/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/8/', endpoint='/dcim/devices/{id}/')]

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
Out[21]: EndpointIdIterator(api=Api, url='https://demo.netbox.dev/api', endpoint='/dcim/devices/')

In [22]: len(all_devices)
Out[22]: 50

In [23]: all_devices[49]
Out[23]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/95/', endpoint='/dcim/devices/')

In [24]: all_devices[49].name
Out[24]: 'ncsu118-distswitch1'

# by default, 'limit' parameter = 50, but you can run 'get' request with custom 'limit'
In [25]: all_devices = await a.dcim_devices(get={"limit": 100})

In [26]: len(all_devices)
Out[26]: 75

In [27]: all_devices[74]
Out[27]: EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/106/', endpoint='/dcim/devices/')

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
[EndpointIdIterator(api=Api, url='https://demo.netbox.dev/api', endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/110/', endpoint='/dcim/devices/'),
 EndpointId(api=Api, url='https://demo.netbox.dev/api/dcim/devices/111/', endpoint='/dcim/devices/')]

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
