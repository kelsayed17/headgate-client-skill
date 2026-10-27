return self.paginate("/v2/%s" % s, expect=BARS, pages=PAGER, limit=LIMIT)
