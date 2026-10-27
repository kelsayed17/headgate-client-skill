# A private Protocol in a client module is not a transport class: its NAME starting `_` does not count.
# Readers moved to module level (R3).
X = decoder(X)


class _Sender(Protocol):
    def send(self, message: str) -> None: ...


class HostClient(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)
