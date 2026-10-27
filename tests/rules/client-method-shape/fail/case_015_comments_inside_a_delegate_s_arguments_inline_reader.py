# Comments inside a delegate's arguments, a header helper's arguments, and a base list; `retry=True`.
# R3: the source's inline reader; `expect=` is a module-level name here.
class HostClient(
    AsyncBaseClient,  # the one base
):
    # a comment in the class body
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T], *, retry: bool = True) -> T:
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload), retry=retry)

    async def get_portfolio(self, arguments: AccountScopedArguments) -> PortfolioPayload:
        return await self._call_tool(
            "get_portfolio",  # the tool's own name
            arguments,
            PortfolioPayload,
            retry=True,
        )

    async def get_account(self, user_id: UUID) -> Account:
        return await self.get(
            "/api/brokerage/account",
            headers=self._uid(
                user_id,  # the acting user
            ),
            expect=decoder(Account),
        )
