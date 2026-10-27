# A lowercase browser token in a User-Agent position is a spoof, the other rule's.
USER_AGENT = "chrome/150.0.0.0"
HEADERS = {"User-Agent": "safari/605.1.15"}
client = C(user_agent="Mozilla/5.0")
