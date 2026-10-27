# The single-page method INJECTED as a parameter: plain, annotated, defaulted, keyword-only, positional-only.
async def follow(fetch, first):
    page = first
    for _ in range(MAX_PAGES):
        page = await fetch(cursor=page.next)
