_HEADERS = {"Accept": "json"}
_HEADERS |= {"Authorization": f"Bearer {KEY}"}
options = HttpOptions(headers=_HEADERS)
