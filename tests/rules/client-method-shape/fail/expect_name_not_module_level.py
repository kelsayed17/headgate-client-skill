# R3: an UPPER_CASE name the module never binds (here a parameter) is not a module-level reader.
class C(AsyncBaseClient):
    async def get_foo(self, FOO: Reader[Foo]) -> Foo:
        return await self.get("foo", expect=FOO)
