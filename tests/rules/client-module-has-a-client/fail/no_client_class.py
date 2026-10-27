"""A client module whose class reaches AsyncBaseClient only through an alias."""

from headgate import AsyncBaseClient as Base


class ExampleClient(Base):
    """No class here names AsyncBaseClient directly in its bases."""
