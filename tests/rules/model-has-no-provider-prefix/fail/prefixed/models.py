# The fixture harness names every package `pkg`, so the provider prefix is `Pkg`.
import msgspec


class PkgFiling(msgspec.Struct, frozen=True):
    id: str
