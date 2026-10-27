from headgate import AsyncBaseClient
from headgate.msgspec import decoder

from .models import Item

ITEM = decoder(Item)
