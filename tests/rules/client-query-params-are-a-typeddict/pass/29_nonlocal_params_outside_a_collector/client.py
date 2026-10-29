def _counter() -> Callable[[], dict[str, int]]:
    params: dict[str, int] = {}

    def bump() -> dict[str, int]:
        nonlocal params
        params = {"n": len(params) + 1}
        return params

    return bump
