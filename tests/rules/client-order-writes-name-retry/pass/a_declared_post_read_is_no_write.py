# headgate-verify-config: {"post_reads": ["search_liquidations", "estimate_multileg_margin"]}
class Broker(AsyncBaseClient):
    async def search_liquidations(self, query: Query) -> Liquidations:
        return await self.post("liquidations/search", body=QUERY(query), expect=LIQUIDATIONS)

    async def estimate_multileg_margin(self, body: MultiLeg) -> Margin:
        return await self.post("margin/estimate", body=MULTI_LEG(body), expect=MARGIN)
