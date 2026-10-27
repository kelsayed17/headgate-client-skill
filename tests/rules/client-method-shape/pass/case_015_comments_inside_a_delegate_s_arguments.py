# Comments inside a delegate's arguments, a header helper's arguments, and a base list; `retry=True`.
# Readers moved to module level (R3); the envelope legs are plain forwards here.
TOOL_RESULT = decoder(ToolResult)


ACCOUNT = decoder(Account)


class HostClient(
    AsyncBaseClient,  # the one base
):
    # a comment in the class body
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T], *, retry: bool = True) -> T:
        return await self.post(t"tools/{name}", body=_WRITE(arguments), expect=TOOL_RESULT, retry=retry)

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
            expect=ACCOUNT,
        )
