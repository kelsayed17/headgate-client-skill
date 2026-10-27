# A module leg on each verb.
# Readers moved to module level (R3).
ACK = decoder(Ack)


async def _post(client: AsyncBaseClient, path: str) -> Ack:
    return await client.post(path, expect=ACK)


async def _put(client: AsyncBaseClient, path: str) -> Ack:
    return await client.put(path, expect=ACK)


async def _patch(client: AsyncBaseClient, path: str) -> Ack:
    return await client.patch(path, expect=ACK)


async def _delete(client: AsyncBaseClient, path: str) -> None:
    return await client.delete(path, expect=nothing)


async def _head(client: AsyncBaseClient, path: str) -> None:
    return await client.head(path, expect=nothing)


class Verbs(AsyncBaseClient):
    async def post_x(self) -> Ack:
        return await _post(self, "x")

    async def put_x(self) -> Ack:
        return await _put(self, "x")

    async def patch_x(self) -> Ack:
        return await _patch(self, "x")

    async def delete_x(self) -> None:
        return await _delete(self, "x")

    async def head_x(self) -> None:
        return await _head(self, "x")
