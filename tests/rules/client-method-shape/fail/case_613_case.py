class C(AsyncBaseClient):
    for _name in ("get_a", "get_b"):
        locals()[_name] = _make(_name)
