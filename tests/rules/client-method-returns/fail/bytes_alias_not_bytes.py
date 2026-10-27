# A module-level chain rooted on `as_bytes` reads raw bytes, so the success arm is `bytes`.
RAW_OR_NONE = Expect(as_bytes).on(404, nothing)


class C(AsyncBaseClient):
    async def get_export(self) -> Export | None:
        return await self.get("export.zip", expect=RAW_OR_NONE)
