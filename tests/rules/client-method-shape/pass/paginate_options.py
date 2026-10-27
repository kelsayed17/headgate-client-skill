# Every option headgate 0.7.0's paginate takes besides the body ones (PageOptions): headers, idempotency_key, timeout,
# deadline, follow_redirects, cache_ttl and retry.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def get_x(
        self, headers: Headers, idempotency_key: str, timeout: Timeouts, **params: Unpack[XParams]
    ) -> Paginated[XPage, XRow]:
        return self.paginate(
            "x",
            params=params,
            headers=headers,
            idempotency_key=idempotency_key,
            timeout=timeout,
            deadline=DEADLINE,
            follow_redirects=False,
            cache_ttl=60.0,
            retry=False,
            expect=X_PAGE,
            pages=X_PAGES,
            limit=MAX_PAGES,
        )
