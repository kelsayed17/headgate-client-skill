# A primitive-valued map (alpaca's four directories and frankfurter's currencies).
# The same case with its readers moved to module level (R3).
STR_STR = decoder(dict[str, str])


class AlpacaDataClient(AsyncBaseClient):
    async def get_stocks_meta_exchanges(self) -> dict[str, str]:
        return await self.get("v2/stocks/meta/exchanges", expect=STR_STR)
