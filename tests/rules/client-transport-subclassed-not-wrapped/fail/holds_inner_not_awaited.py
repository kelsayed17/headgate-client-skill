class PassThrough(httpx2.AsyncBaseTransport):
    def __init__(self, inner) -> None:
        self._inner = inner

    def handle_async_request(self, request):
        return self._inner.handle_async_request(request)
