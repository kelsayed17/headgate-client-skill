results = await asyncio.gather(*[self.get(f"/v2/{s}") for s in symbols])
