class Plain(httpx2.AsyncHTTPTransport):
    async def handle_async_request(self, request):
        base = super()
        return await base.handle_async_request(request)
