# Not directly in the class body: a method body, an `if` under the class, a module statement.
class C:
    def m(self) -> None:
        X_PATH = "/x"
        self.Y_PATH = "/y"

    if TYPE_CHECKING:
        Z_PATH = "/z"

W_PATH = "/w"
