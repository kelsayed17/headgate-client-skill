class C(AsyncBaseClient):
    get_x: Callable[..., Awaitable[X]] = _make("x")
