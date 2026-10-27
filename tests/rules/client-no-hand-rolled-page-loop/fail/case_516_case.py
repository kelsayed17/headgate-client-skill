async def follow(*, limit: int = 5, fetch: Fetch | None = None):
    while True:
        await fetch()
