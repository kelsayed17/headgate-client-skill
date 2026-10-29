class C(AsyncBaseClient):
    async def stream_x(self, **params: Unpack[XParams]) -> AsyncIterator[bytes]:
        count = 0
        count += 1
        if (n := len(params)) > 1:
            pass
        for key in params:
            _seen[key] = n
        del _seen["x"]
        _log(list(params.keys()), list(params.values()), list(params.items()))
        async with self.stream("x", params=params) as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
