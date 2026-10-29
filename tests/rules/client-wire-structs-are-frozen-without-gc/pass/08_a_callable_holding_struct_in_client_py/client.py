from collections.abc import Callable

from msgspec import Struct


class Hooks(Struct, frozen=True):
    on_page: Callable[[int], None]


class Widgets(AsyncBaseClient):
    def __init__(self) -> None:
        self._hooks = Hooks(on_page=self.tick)
