# `-> str` from a module-level decoder.
STR = decoder(str)


class C(AsyncBaseClient):
    async def get_report(self) -> str:
        return await self.get("report", expect=STR)
