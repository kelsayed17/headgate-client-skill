# `bytes | None` with a reader that declares the `nothing` answer: the None is honest, the bytes are not.
from http import HTTPStatus


class C(AsyncBaseClient):
    async def get_export(self) -> bytes | None:
        return await self.get("export.zip", expect=Expect(as_bytes).on(HTTPStatus.NOT_FOUND, nothing))
