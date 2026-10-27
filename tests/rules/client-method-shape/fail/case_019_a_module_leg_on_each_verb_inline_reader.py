# A module leg on each verb.
# R3: the source's inline reader; `expect=` is a module-level name here.
async def _post(client: AsyncBaseClient, path: str) -> Ack:
    return await client.post(path, expect=decoder(Ack))


async def _put(client: AsyncBaseClient, path: str) -> Ack:
    return await client.put(path, expect=decoder(Ack))


async def _patch(client: AsyncBaseClient, path: str) -> Ack:
    return await client.patch(path, expect=decoder(Ack))


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
