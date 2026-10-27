# R3: a reader built at the call. Readers are module-level values, so `expect=` is a bare UPPER_CASE name.
class C(AsyncBaseClient):
    async def get_foo(self) -> Foo:
        return await self.get("foo", expect=decoder(Foo))
