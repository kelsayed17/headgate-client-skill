# A module-level reader decoding into Any is an untyped decode, wherever it is used.
READER = decoder(Any)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=READER)
