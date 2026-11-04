# R3: a reader named at module level is reported inside an Expect root too: every reader is written at the call.
FOO = decoder(Foo)


class C(AsyncBaseClient):
    async def get_foo(self) -> Foo | None:
        return await self.get("foo", expect=Expect(FOO).on(HTTPStatus.NOT_FOUND, nothing))
