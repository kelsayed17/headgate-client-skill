# `Pkgsite` starts with the letters of `Pkg` but not with the word: a lowercase letter follows.
import msgspec


class Pkgsite(msgspec.Struct, frozen=True):
    url: str
