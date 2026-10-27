self.paginate(  # walk every page
    t"/x/{y}",
    expect=BARS,
    pages=PAGER,
    limit=LIMIT,
)
