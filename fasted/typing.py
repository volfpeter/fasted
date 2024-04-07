from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, Concatenate, Coroutine, ParamSpec, Protocol, TypeVar

Tcov = TypeVar("Tcov", covariant=True)

TOwner = TypeVar("TOwner")
TResult = TypeVar("TResult")
TParams = ParamSpec("TParams")

BoundMethod = Callable[Concatenate[TOwner, TParams], TResult]


class Dependency(Protocol[Tcov]):
    """Generic FastAPI dependency function protocol."""

    def __call__(
        self, *args: Any, **kwargs: Any
    ) -> Tcov | Coroutine[Any, Any, Tcov] | Generator[Tcov, Any, Any] | AsyncGenerator[Tcov, Any]: ...
