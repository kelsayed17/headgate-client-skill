async def follow_absolute(client, url):
    while url:
        page = await client.get(url)
        url = page.next
