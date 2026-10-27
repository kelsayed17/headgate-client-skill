# The transport knobs (retry=, follow_redirects=, cache_ttl=) as a literal or a parameter, timeout= as a parameter or
# a module constant (a literal is not a `Timeouts`, headgate 0.6.0); a forwarded
# parameter defaulting to None; the allowed dunders.
# R3: the source's inline reader; `expect=` is a module-level name here.
class Knobs(AsyncBaseClient):
    def __init__(self, *, timeout: float = 30.0) -> None:
        super().__init__(base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC))

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def get_x(self, retry: bool, timeout: float, cache_ttl: float, body: Body | None = None) -> X:
        return await self.post(
            "x",
            json=body,
            retry=retry,
            timeout=timeout,
            follow_redirects=False,
            cache_ttl=cache_ttl,
            expect=decoder(X),
        )

    async def get_y(self) -> Y:
        return await self.get("y", retry=True, timeout=_SHORT, follow_redirects=True, expect=decoder(Y))
