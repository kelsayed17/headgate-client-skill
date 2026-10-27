# A decoded model, a list of them, a map of them, a generic model.
# The same case with its readers moved to module level (R3).
AGGS_ENVELOPE = decoder(AggsEnvelope)
POSITION = decoder(list[Position])
STR_SNAPSHOT = decoder(dict[str, Snapshot])
STR_BAR = decoder(dict[str, list[Bar]])


class MassiveClient(AsyncBaseClient):
    async def get_aggs(self, ticker: str, **params: Unpack[AggsParams]) -> AggsEnvelope:
        return await self.get(t"v2/aggs/ticker/{ticker}", params=params, expect=AGGS_ENVELOPE)

    async def get_positions(self) -> list[Position]:
        return await self.get("v2/positions", expect=POSITION)

    async def get_snapshots(self, **params: Unpack[SnapshotParams]) -> dict[str, Snapshot]:
        return await self.get("v1beta1/options/snapshots", params=params, expect=STR_SNAPSHOT)

    async def get_bars(self, **params: Unpack[BarsParams]) -> dict[str, list[Bar]]:
        return await self.get("v2/stocks/bars", params=params, expect=STR_BAR)
