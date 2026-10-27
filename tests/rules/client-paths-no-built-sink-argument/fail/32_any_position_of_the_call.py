def _walk(client, s):
    return client.paginate(  # the walk
        # the path
        "/v2/" + s,
        expect=BARS,
        pages=PAGER,
        limit=LIMIT,
    )
