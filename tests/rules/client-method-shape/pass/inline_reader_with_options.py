# R3: a reader built with an option is named at module level. The option is a decision about the answer
# (`strict=False`, `allow_empty_body=True`, `refusal_check=`), and the name is where it is read.
class C(AsyncBaseClient):
    async def get_lax(self) -> Foo:
        return await self.get("lax", expect=decoder(Foo, strict=False))

    async def get_maybe_empty(self) -> list[Row]:
        return await self.get("rows", expect=adapter(list[Row], allow_empty_body=True))

    async def get_checked(self) -> Status:
        return await self.get("status", expect=decoder(Status, refusal_check=_check))
