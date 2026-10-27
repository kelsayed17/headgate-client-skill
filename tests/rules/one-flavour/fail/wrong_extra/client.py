from headgate import AsyncBaseClient
from headgate.pydantic import decoder

from .models import Item

ITEM = decoder(Item)
