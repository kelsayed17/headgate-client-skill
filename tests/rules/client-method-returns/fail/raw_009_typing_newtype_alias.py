# `typing.NewType` over `str`.
import typing

Token = typing.NewType("Token", str)


class C(AsyncBaseClient):
    async def get_token(self) -> Token:
        return await self.get("token", expect=decoder(Token))
