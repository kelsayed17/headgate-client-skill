class _Pages:
    def next_page(self, page: Page, request: PageRequest) -> PageRequest | None:
        params = request.params or {}
        return request.with_param("offset", int(str(params["offset"])) + len(page))
