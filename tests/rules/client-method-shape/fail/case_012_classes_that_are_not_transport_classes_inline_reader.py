# Classes that are not transport classes, anywhere in the module.
# R3: the source's inline reader; `expect=` is a module-level name here.
class AsgiApp(Protocol):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None: ...


class OrderDeclined(ClientError):
    """The engine declined."""

    def describe(self) -> str:
        return "declined"

    @property
    def text(self) -> str:
        return self.render()


class _TokenAuth(httpx.Auth):
    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response]:
        yield request


@functools.cache
def default_identity() -> str:
    return "PaperServer/1.0"


def house_fd_xml_path(year: int) -> Template:
    return t"public_disc/financial-pdfs/{year}FD.xml"


class HostClient(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=decoder(X))

    # a comment between two methods is not a statement

    async def get_y(self) -> Y:
        return await self.get("y", expect=decoder(Y))
