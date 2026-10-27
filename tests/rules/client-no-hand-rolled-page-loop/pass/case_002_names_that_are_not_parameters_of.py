# Names that are not parameters of an enclosing def: `*args`/`**kwargs`, a type annotation, a default VALUE, a
# lambda's parameter, another function's parameter; an injected client's non-verb method.
async def splat(*fetch, **get):
    while True:
        await fetch()
        await get()


async def annotated(x: fetch, y=get, cb=lambda post: post):
    while True:
        await fetch()
        await get()
        await post()


def other(put):
    return put


async def walk(client):
    while True:
        await put()
        await client.close()
