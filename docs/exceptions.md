## Request and Response exceptions

`anac` is based on `httpx`, so `httpx` exceptions are available here. 
See <a href="https://github.com/encode/httpx/blob/master/httpx/_exceptions.py" target="_blank">`httpx._exceptions`</a> and <a href="https://www.python-httpx.org/exceptions/" target="_blank">https://www.python-httpx.org/exceptions/</a>

## Anac exception classes

::: anac.RequestDataError
    :docstring:

::: anac.RequestParamsError
    :docstring:

<a href="https://www.python-httpx.org/quickstart/" target="_blank">The difference between data and parameters</a> 

::: anac.raise_for_status
    :docstring:

`anac.raise_for_status` is a classic <a href="https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1475" target="_blank">`httpx.Response.raise_for_status()`</a> function, but with minor changes. As instance:
```python
In [1]: from anac import api
   ...: 
   ...: a = api(
   ...:     "https://demo.netbox.dev",
   ...:     token="cf1dc7b04de5f27cfc93aba9e3f537d2ad6fdf8c",
   ...: )
   ...: # get openapi spec and create attributes/endpoints
   ...: # with python interpreter autocompletion
   ...: await a.openapi()

In [2]: test3_device = await a.dcim_device(
   ...:     post={
   ...:         "name": "test3",
   ...:         "device_role": {"name": 1},
   ...:         "site": {"name": "DM-Rochester"},
   ...:         "device_type": {"model": "C9200-48P"},
   ...:         "status": "planned",
   ...:     }
   ...: )

HTTPStatusError: Client error '400 Bad Request' (see https://httpstatuses.com/400) for url 'https://demo.netbox.dev/api/dcim/devices/' and 'POST' method.
Request parameters:
{"name": "test3", "device_role": {"name": 1}, "site": {"name": "DM-Rochester"}, "device_type": {"model": "C9200-48P"}, "status": "planned"}
Response:
{'device_role': ["Related object not found using the provided attributes: {'name': 1}"]}
```
