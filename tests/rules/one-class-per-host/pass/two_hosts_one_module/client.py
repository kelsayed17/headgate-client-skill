# Review Focus 2: one provider, two hosts, one module. Each host has its own class and its own module-level base URL
# name; the module-level helpers (rate, readers, a header builder) are shared as values, not through a base class.
from headgate import AsyncBaseClient, HttpOptions, Rate
from headgate.msgspec import decoder

WWW = "https://www.filings.example"
DATA = "https://data.filings.example"
RATE = Rate(10)
FILING_INDEX = decoder(FilingIndex)
COMPANY_FACTS = decoder(CompanyFacts)


def _http(user_agent: str, transport: AsyncBaseTransport | None) -> HttpOptions:
    return HttpOptions(headers={"User-Agent": user_agent}, transport=transport)


class Www(AsyncBaseClient):
    def __init__(self, user_agent: str, transport: AsyncBaseTransport | None = None) -> None:
        super().__init__(base_url=WWW, rate=RATE, http=_http(user_agent, transport))

    async def get_cgi_bin_browse_edgar(self, **params: Unpack[BrowseParams]) -> FilingIndex:
        return await self.get("cgi-bin/browse-edgar", params=params, expect=FILING_INDEX)

    async def get_full_index(self) -> FilingIndex:
        return await self.get("https://www.filings.example/Archives/full-index/", expect=FILING_INDEX)


class Data(AsyncBaseClient):
    def __init__(self, user_agent: str, transport: AsyncBaseTransport | None = None) -> None:
        super().__init__(base_url=DATA, rate=RATE, http=_http(user_agent, transport))

    async def get_company_facts(self, cik: str) -> CompanyFacts:
        return await self.get(t"api/xbrl/companyfacts/CIK{cik}.json", expect=COMPANY_FACTS)
