# A closure over an outer def's parameter (any number of defs up, through a class); the CLIENT injected.
def make(get):
    async def inner():
        for _ in range(5):
            await get()

    return inner
