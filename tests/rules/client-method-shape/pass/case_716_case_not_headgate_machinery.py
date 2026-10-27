# An in-tree base's old request-method name means nothing to headgate 0.7.0: defining it is a private helper.
class C(AsyncBaseClient):
    @traced
    async def _send(self, method: str, path: str, **kwargs: Any) -> Any:
        return await super()._send(method, path, **kwargs)
