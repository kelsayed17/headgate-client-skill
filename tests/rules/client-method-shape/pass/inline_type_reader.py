# R3: a plain type reader written at the call. `decoder(Type)` with no option says nothing a name would add, so it may
# sit in `expect=` instead of at module level.
class C(AsyncBaseClient):
    async def get_foo(self) -> Foo:
        return await self.get("foo", expect=decoder(Foo))
