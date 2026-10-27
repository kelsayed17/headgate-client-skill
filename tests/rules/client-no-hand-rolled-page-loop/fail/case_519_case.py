def make(get):
    class Walker:
        async def run(self):
            while True:
                await get()

    return Walker
