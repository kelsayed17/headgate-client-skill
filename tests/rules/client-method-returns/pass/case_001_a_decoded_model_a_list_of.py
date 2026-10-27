# A decoded model, a list of them, a map of them, a generic model.
class MassiveClient(AsyncBaseClient):
    async def get_aggs(self, ticker: str, **params: Unpack[AggsParams]) -> AggsEnvelope:
        return await self.get(t"v2/aggs/ticker/{ticker}", params=params, expect=decoder(AggsEnvelope))

    async def get_positions(self) -> list[Position]:
        return await self.get("v2/positions", expect=decoder(list[Position]))

    async def get_snapshots(self, **params: Unpack[SnapshotParams]) -> dict[str, Snapshot]:
        return await self.get("v1beta1/options/snapshots", params=params, expect=decoder(dict[str, Snapshot]))

    async def get_bars(self, **params: Unpack[BarsParams]) -> dict[str, list[Bar]]:
        return await self.get("v2/stocks/bars", params=params, expect=decoder(dict[str, list[Bar]]))
