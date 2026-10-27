from string.templatelib import Template

def _orders(order_id: str) -> Template:
    return t"/orders/{order_id}/"
