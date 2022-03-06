import httpx
from json import JSONDecodeError


class RequestDataError(Exception):
    """For invalid http request data
    """
    def __init__(self, message: str, method: str) -> None:
        super().__init__(message)
        self.message = message
        self.method = method

    def __str__(self) -> str:
        return f"Passing Data error for {self.method.upper()} method. {self.message}"


class RequestParamsError(Exception):
    """For invalid http request params
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"Passing Parameters error for GET method. {self.message}"


# classic httpx.Response.raise_for_status() function, but with minor changes
# https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1475
def raise_for_status(response: httpx.Response) -> None:
    """Raise the `HTTPStatusError` if one occurred.
    """
    request = response._request
    if request is None:
        raise RuntimeError(
            "Cannot call `raise_for_status` as the request "
            "instance has not been set on this response."
        )

    if response.is_success:
        return

    if response.has_redirect_location:
        message = (
            "{error_type} '{0.status_code} {0.reason_phrase}' for url '{0.url}'\n"
            "Redirect location: '{0.headers[location]}'\n"
            "For more information check: https://httpstatuses.com/{0.status_code}"
        )
    else:
        message = (
            "{error_type} '{0.status_code} {0.reason_phrase}' "
            "(see https://httpstatuses.com/{0.status_code}) "
            "for url '{0.url}' and '{0.request.method}' method.\n"
            "Request parameters:\n"
            "{parameters}\n"
            "Response:\n"
            "{response_json}\n"
        )

    status_class = response.status_code // 100
    error_types = {
        1: "Informational response",
        3: "Redirect response",
        4: "Client error",
        5: "Server error",
    }
    error_type = error_types.get(status_class, "Invalid status code")
    try:
        message = message.format(
            response,
            error_type=error_type,
            parameters=response.request.content.decode("utf-8"),
            response_json=response.json(),
        )
    except JSONDecodeError:
        raise httpx.DecodingError("The server returned non json data")
    raise httpx.HTTPStatusError(message, request=request, response=response)
