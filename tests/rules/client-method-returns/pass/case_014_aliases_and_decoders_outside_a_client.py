# Aliases and decoders outside a client module are not read; a type alias of an allowed type is fine; a class
# attribute naming str in a non-transport class is not a module alias; a string constant is not a type.
Payload = Any
_DEC = decoder(Any)
