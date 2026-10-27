class Quote(msgspec.Struct):
    @staticmethod
    @functools.cache
    def parse(raw: bytes) -> Quote:
        return msgspec.json.decode(raw, type=Quote)
