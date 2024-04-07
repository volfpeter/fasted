import inspect
from collections.abc import Callable
from typing import ParamSpec, TypeVar

Tcov = TypeVar("Tcov", covariant=True)
TOwner = TypeVar("TOwner")
TResult = TypeVar("TResult")
TParams = ParamSpec("TParams")


def replace_self_signature(
    func: Callable[TParams, TResult],
    self_param: inspect.Parameter,
) -> Callable[TParams, TResult]:
    """
    Replaces the signature of the `self` argument of `func` with the given one.

    Arguments:
        func: The function whose self argument should be replaced.
        self_param: The new parameter description for the `self` argument.

    Returns:
        The received function with the updated annotations.

    Raises:
        ValueError: If `func` has no `self` argument.
    """
    signature = inspect.signature(func)
    if "self" not in signature.parameters:
        raise ValueError("Method has no self argument.")

    func.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=(
            self_param,
            *(v for k, v in signature.parameters.items() if k != "self"),
        )
    )
    return func
