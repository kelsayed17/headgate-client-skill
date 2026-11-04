# `builtins.bytes` is `bytes`.
import builtins


class C(AsyncBaseClient):
    async def get_report(self) -> builtins.bytes:
        return await self.get("report", expect=decoder(builtins.bytes))
