# R3: a reader bound in a function, not at module level.
def _setup() -> None:
    FOO = decoder(Foo)


class C(AsyncBaseClient):
    async def get_foo(self) -> Foo:
        return await self.get("foo", expect=FOO)
