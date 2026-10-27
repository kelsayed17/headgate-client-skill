# A branch before the request (congress:122).
class HouseClerkClient(AsyncBaseClient):
    async def check_available(self, year: int | None = None) -> None:
        if year is None:
            year = datetime.now(UTC).year
        await self.head(house_fd_xml_path(year), expect=nothing, timeout=10)
