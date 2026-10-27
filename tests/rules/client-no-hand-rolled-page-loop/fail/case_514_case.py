async def follow(fetch: Callable[..., Awaitable[Page]]) -> None:
    while True:
        await fetch()
