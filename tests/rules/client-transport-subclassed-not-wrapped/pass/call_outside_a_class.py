async def send(inner, request):
    return await inner.handle_async_request(request)
