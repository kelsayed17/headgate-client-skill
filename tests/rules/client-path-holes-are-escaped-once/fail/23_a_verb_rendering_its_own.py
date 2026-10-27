return self.paginate(render_path(t"/orders/{o}"), expect=ORDERS, pages=PAGER, limit=LIMIT)
