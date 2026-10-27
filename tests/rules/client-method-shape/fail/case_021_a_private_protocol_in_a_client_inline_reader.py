# A private Protocol in a client module is not a transport class: its NAME starting `_` does not count.
# R3: the source's inline reader; `expect=` is a module-level name here.
class _Sender(Protocol):
    def send(self, message: str) -> None: ...


class HostClient(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=decoder(X))
