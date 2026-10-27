# R3: a dotted name is not a bare one.
class C(AsyncBaseClient):
    async def get_foo(self) -> Foo:
        return await self.get("foo", expect=readers.FOO)
