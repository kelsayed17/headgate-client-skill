# R3: a reader under a lowercase name.
foo_reader = decoder(Foo)


class C(AsyncBaseClient):
    async def get_foo(self) -> Foo:
        return await self.get("foo", expect=foo_reader)
