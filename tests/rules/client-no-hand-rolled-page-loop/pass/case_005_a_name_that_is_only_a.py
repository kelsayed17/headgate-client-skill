# A name that is only a typed default's VALUE; a parameter of a def nested in the enclosing one (not enclosing the
# loop); a parameter named like a verb, used as neither the client nor the callee.
async def typed(x: Fetch = get):
    while True:
        await get()


async def m(self):
    def helper(fetch):
        return fetch

    while True:
        await fetch()


async def walk(get):
    while True:
        await session.get("/x")
        await get.close()
