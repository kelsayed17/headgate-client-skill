# R3: an inline reader's argument is a type expression. A parameter, a local or a call is a reader built per call.
class C(AsyncBaseClient):
    async def get_any(self, model: type[T]) -> T:
        return await self.get("any", expect=decoder(model))

    async def get_made(self) -> Foo:
        return await self.get("made", expect=decoder(model_for("made")))

    async def get_list_of_param(self, row: type[T]) -> list[T]:
        return await self.get("rows", expect=decoder(list[row]))

    async def get_two(self) -> Foo:
        return await self.get("two", expect=decoder(Foo, Bar))
