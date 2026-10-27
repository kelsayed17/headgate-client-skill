# A try around the request.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        try:
            return await self.get("x", expect=X)
        except ClientError:
            raise
