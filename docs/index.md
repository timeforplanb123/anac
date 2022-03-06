<h1 align="center" style="font-size: 3rem; margin: -15px 0">
ANAC
</h1>

---
<div align="center">
<h2><b>A</b>sync <b>N</b>etBox <b>A</b>PI <b>C</b>lient</h2>
</div>


**anac** - is a simple Python <a href="https://github.com/netbox-community/netbox" target="_blank">NetBox</a> API client with async interface and based on awesome <a href="https://github.com/encode/httpx" target="_blank">httpx</a> and <a href="https://nornir.tech/nornir/plugins/" target="_blank">pydantic</a>


## Features 

* Minimalistic interface
* Async only
* Python interpreter autocompletion
* Supports <a href="https://github.com/netbox-community/netbox" target="_blank">NetBox</a> 2.x, 3.x
* Flexibility. All the objects are coroutines or coroutine iterators
* Simple integration with parsers (<a href="https://github.com/google/textfsm" target="_blank">TextFSM</a>, <a href="https://github.com/dmulyalin/ttp" target="_blank">TTP</a>)

## Installation

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

## Simple Example

**Api Instantiating**
```python
from anac import api

a = api(
    "https://demo.netbox.dev",
    token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
)
# get openapi spec and create attributes/endpoints   
await a.openapi()
```
**`get` some device and `patch` it**
```python
# get some device from NetBox
In [1]: some_device = await a.dcim_devices(get={"name": "dmi01-rochster-sw01"})

# check some attributes
In [2]: some_device.name
Out[2]: 'dmi01-rochster-sw01'

In [3]: some_device.device_type.model
Out[3]: 'C9200-48P'

# 'patch' some_device status
In [4]: some_device = await some_device(patch={"status": "failed"})

# check new status
In [5]: some_device.status
Out[5]: {'value': 'failed', 'label': 'Failed'}
```

[![asciicast](https://asciinema.org/a/DmirYBxwl40VP9Delp6e0J3dE.svg)](https://asciinema.org/a/DmirYBxwl40VP9Delp6e0J3dE)
