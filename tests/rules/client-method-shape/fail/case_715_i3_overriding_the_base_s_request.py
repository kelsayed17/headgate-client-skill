# I3: overriding the base's request machinery.
class C(AsyncBaseClient):
    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        return await super()._request(method, url, **kwargs)
