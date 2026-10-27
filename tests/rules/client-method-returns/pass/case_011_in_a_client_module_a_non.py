# In a client module: a non-transport class, lifecycle, a decorated module function, a Response parameter.
class OrderDeclined(ClientError):
    def describe(self) -> str:
        return "declined"


@functools.cache
def default_identity() -> str:
    return "PaperServer/1.0"


def _status(resp: httpx2.Response) -> int:
    return resp.status_code


class HostClient(AsyncBaseClient):
    async def aclose(self) -> None:
        await self._other.aclose()
