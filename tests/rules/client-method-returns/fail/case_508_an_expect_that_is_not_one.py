# An expect that is not one of the house readers.
class C(AsyncBaseClient):
    async def get_events(self) -> list[bytes]:
        return await self.get("events", expect=event_stream)
