# `typing.Text` is `str`.
import typing


class C(AsyncBaseClient):
    async def get_report(self) -> typing.Text:
        return await self.get("report", expect=decoder(typing.Text))
