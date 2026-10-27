# R3: a documented answer declared at the call; it is declared at module level, beside the reader it extends.
FOO = decoder(Foo)


class C(AsyncBaseClient):
    async def get_foo(self) -> Foo | None:
        return await self.get("foo", expect=Expect(FOO).on(HTTPStatus.NOT_FOUND, nothing))
