# A comment before the statement, and between the docstring and the statement.
class SecFilesClient(AsyncBaseClient):
    async def fetch_ptr_pdf(self, pdf_url: str) -> bytes:
        # the absolute URL carried on the filing record
        return await self.get(pdf_url, expect=as_bytes)

    async def fetch_house_fd_xml(self, year: int) -> bytes:
        """One year's index."""
        # 403 and 404 mean nothing is published yet
        # (a second comment line)
        return await self.get(house_fd_xml_path(year), expect=as_bytes)
