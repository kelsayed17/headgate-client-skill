class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        def build() -> dict[str, str]:
            params = {"kind": "x"}
            return params

        pick = lambda params: params.pop("kind")
        return await self.get("x", params=params, expect=decoder(X))
