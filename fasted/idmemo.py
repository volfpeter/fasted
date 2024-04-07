from typing import Any, Generic

from .typing import TResult as TMemo


class IdMemo(Generic[TMemo]):
    """Simple memo class that uses `id()` for hash calculation."""

    __slots__ = ("_hash", "_value")

    def __init__(self) -> None:
        """Initialization."""
        self._hash: int | None = None
        self._value: TMemo | None = None

    def __contains__(self, key: int) -> bool:
        return self._hash == key

    @property
    def value(self) -> TMemo:
        """The current value in the memo."""
        if self._value is None:
            raise KeyError("Memo value accessed before first use.")

        return self._value

    def store(self, key: int, value: TMemo) -> TMemo:
        """
        Stores the given value in the memo.

        Arguments:
            key: The calculated key (hash) for the given `value`.
            value: The value to store in the memo.

        Returns:
            The received `value`.
        """
        self._hash = key
        self._value = value
        return value

    def hash(self, *items: Any) -> int:
        """Calculates the hash of the positional arguments using the `id()` function."""
        return hash(tuple(id(i) for i in items))
