headers = {"X-Token": token}
_SAFE = {"Accept": "json"}
await client.get("/x", headers=headers, expect=as_bytes)
merged = _SAFE | {"X-Token": token}
HttpOptions(headers=_SAFE)
