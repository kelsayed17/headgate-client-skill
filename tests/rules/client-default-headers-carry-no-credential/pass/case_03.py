client = AsyncBaseClient(base_url=_BASE_URL, auth=StaticHeaderAuth({"Authorization": f"Bearer {key}"}))
await client.get("/x", headers={"Authorization": f"Bearer {key}"}, expect=as_bytes)
await client.get("/x", expect=Expect(as_bytes, headers={"X-Token": key}))
session = httpx2.AsyncClient(headers={"Authorization": f"Bearer {key}"})
opts = Options(headers={"X-Api-Key": key})
# Another HttpOptions keyword: only headers= is a default header set.
tagged = HttpOptions(headers={"Accept": "json"}, transport=_recording({"Authorization": key}))
