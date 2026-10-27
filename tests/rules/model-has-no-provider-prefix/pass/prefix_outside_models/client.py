# The rule reads models.py only; a client class may carry the provider's name.
from headgate import AsyncBaseClient


class PkgClient(AsyncBaseClient):
    pass
