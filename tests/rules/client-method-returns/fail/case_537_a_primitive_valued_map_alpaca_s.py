# A primitive-valued map (alpaca's four directories and frankfurter's currencies).
class AlpacaDataClient(AsyncBaseClient):
    async def get_stocks_meta_exchanges(self) -> dict[str, str]:
        return await self.get("v2/stocks/meta/exchanges", expect=decoder(dict[str, str]))
