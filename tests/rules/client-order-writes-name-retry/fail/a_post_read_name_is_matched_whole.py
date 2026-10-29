# headgate-verify-config: {"post_reads": ["search_liquidations"]}
class Broker(AsyncBaseClient):
    async def search_liquidations_and_close(self, body: Close) -> Order:
        return await self.post("liquidations/close", body=CLOSE(body), expect=ORDER)
