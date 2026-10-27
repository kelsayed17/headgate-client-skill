return self.paginate(f"/v2/{s}/bars", expect=BARS, pages=PAGER, limit=LIMIT)
