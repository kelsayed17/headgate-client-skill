# Lowercase tokens count only in a User-Agent position; a path or value literal is not one.
ORDERS = "orders/123"
REPORTS = "reports/2024"
JOINED_PATH = "x" "orders/1"
NOTE = "key; value/9"
PATHS = {"path": "orders/123", "Accept": "reports/2024"}
await client.get("reports/2024", expect=_REPORT)
CLAUSE = ("key; value/9")
JOINED_CLAUSE = "key" "; value/9"
COMPAT = "Mozilla/5.0 (compatible; acme-bot/2.1)"
