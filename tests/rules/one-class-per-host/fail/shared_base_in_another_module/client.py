# The client class subclasses a client base from a sibling module.
from headgate import AsyncBaseClient

from .base import Base

API = "https://api.one.example"


class Client(Base):
    def __init__(self) -> None:
        super().__init__(API)
