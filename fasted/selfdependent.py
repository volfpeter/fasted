import asyncio
import inspect
from collections.abc import AsyncGenerator, Callable, Generator
from functools import wraps
from typing import Annotated, Any, Concatenate, Coroutine, Generic, overload

from fastapi import Depends

from .idmemo import IdMemo
from .typing import BoundMethod, Dependency, TOwner, TParams, TResult
from .utils import replace_self_signature


class SelfWrapper:
    """
    `SelfDependent` function wrappers that populate the `self` argument of the wrapped function
    from the keyword arguments (if one was provided), or use the owner instance if one wasn't
    provided. Thus the wrapped "static" methods can behave as if they were instance methods.
    """

    @classmethod
    def sync_method(
        cls,
        func: Callable[Concatenate[TOwner, TParams], TResult],
        owner: TOwner | None,
    ) -> Callable[TParams, TResult]:
        """
        Wrapper for synchronous methods.

        Arguments:
            func: The function to wrap.
            owner: An optional owner object.

        Returns:
            The wrapper.
        """

        @wraps(func)
        def do(*args: TParams.args, **kwargs: TParams.kwargs) -> TResult:
            func_self: TOwner = kwargs.pop("self") if "self" in kwargs else owner  # type: ignore[assignment]
            if func_self is None:
                raise RuntimeError("Missing self argument.")

            return func(func_self, *args, **kwargs)

        return do

    @classmethod
    def sync_generator(
        cls,
        func: Callable[Concatenate[TOwner, TParams], Generator[TResult, Any, Any]],
        owner: TOwner | None,
    ) -> Callable[TParams, Generator[TResult, None, None]]:
        """
        Wrapper for synchronous generator methods.

        Arguments:
            func: The function to wrap.
            owner: An optional owner object.

        Returns:
            The wrapper.
        """

        @wraps(func)
        def do(*args: TParams.args, **kwargs: TParams.kwargs) -> Generator[TResult, None, None]:
            func_self: TOwner = kwargs.pop("self") if "self" in kwargs else owner  # type: ignore[assignment]
            if func_self is None:
                raise RuntimeError("Missing self argument.")

            yield from func(func_self, *args, **kwargs)

        return do

    @classmethod
    def async_method(
        cls,
        func: Callable[Concatenate[TOwner, TParams], Coroutine[None, None, TResult]],
        owner: TOwner | None,
    ) -> Callable[TParams, Coroutine[None, None, TResult]]:
        """
        Wrapper for asynchronous methods.

        Arguments:
            func: The function to wrap.
            owner: An optional owner object.

        Returns:
            The wrapper.
        """

        @wraps(func)
        async def do(*args: TParams.args, **kwargs: TParams.kwargs) -> TResult:
            func_self: TOwner = kwargs.pop("self") if "self" in kwargs else owner  # type: ignore[assignment]
            if func_self is None:
                raise RuntimeError("Missing self argument.")

            return await func(func_self, *args, **kwargs)

        return do

    @classmethod
    def async_generator(
        cls,
        func: Callable[
            Concatenate[TOwner, TParams],
            AsyncGenerator[TResult, None],
        ],
        owner: TOwner | None,
    ) -> Callable[TParams, AsyncGenerator[TResult, None]]:
        """
        Wrapper for asynchronous generator methods.

        Arguments:
            func: The function to wrap.
            owner: An optional owner object.

        Returns:
            The wrapper.
        """

        @wraps(func)
        async def do(*args: TParams.args, **kwargs: TParams.kwargs) -> AsyncGenerator[TResult, None]:
            func_self: TOwner = kwargs.pop("self") if "self" in kwargs else owner  # type: ignore[assignment]
            if func_self is None:
                raise RuntimeError("Missing self argument.")

            async for res in func(func_self, *args, **kwargs):
                yield res

        return do


class SelfDependent(Generic[TOwner, TParams, TResult]):
    """
    Descriptor whose value is a method (FastAPI dependency) with an annotated
    `self` argument that can be processed and used by FastAPI as a dependency.
    """

    __slots__ = ("_wrapped", "_factory", "_memo")

    def __init__(
        self,
        wrapped: Callable[Concatenate[TOwner, TParams], TResult],
        *,
        factory: Dependency[TOwner] | None = None,
    ) -> None:
        """
        Initialization.

        Arguments:
            wrapped: The wrapped function.
            factory: An optional factory for creating `self` instances.
        """
        self._wrapped = wrapped
        self._factory = factory
        self._memo = IdMemo[Callable[TParams, TResult]]()

    def __get__(self, owner: TOwner | None, obj_type: type[TOwner]) -> Callable[TParams, TResult]:
        memo = self._memo
        hcurrent = memo.hash(owner, obj_type)
        if hcurrent in memo:
            return self._memo.value

        result: Callable[TParams, TResult]
        wrapped = self._wrapped
        if inspect.isgeneratorfunction(wrapped):
            result = SelfWrapper.sync_generator(wrapped, owner)  # type: ignore[assignment]
        elif inspect.isasyncgenfunction(wrapped):
            result = SelfWrapper.async_generator(wrapped, owner)  # type: ignore[assignment]
        elif asyncio.iscoroutinefunction(wrapped):
            result = SelfWrapper.async_method(wrapped, owner)  # type: ignore[assignment]
        else:
            result = SelfWrapper.sync_method(wrapped, owner)

        replace_self_signature(
            result,
            inspect.Parameter(
                "self",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Annotated[obj_type, Depends(self._factory or obj_type)],
            ),
        )

        return self._memo.store(hcurrent, result)


@overload
def selfdependent(
    factory: None = None,
) -> Callable[[BoundMethod[TOwner, TParams, TResult]], SelfDependent[TOwner, TParams, TResult]]: ...


@overload
def selfdependent(
    factory: Dependency[TOwner],
) -> Callable[[BoundMethod[TOwner, TParams, TResult]], SelfDependent[TOwner, TParams, TResult]]: ...


def selfdependent(
    factory: Dependency[TOwner] | None = None,
) -> Callable[[BoundMethod[TOwner, TParams, TResult]], SelfDependent[TOwner, TParams, TResult]]:
    """
    Decorator that converts an instance method into a FastAPI dependency using a `SelfDependent` descriptor.

    Arguments:
        factory: An optional factory (and FastAPI dependency) that can be wrapped in `Depends()`
            and that produces the `self` argument for the wrapped method.
    """

    def decorator(
        func: Callable[Concatenate[TOwner, TParams], TResult],
    ) -> SelfDependent[TOwner, TParams, TResult]:
        return SelfDependent[TOwner, TParams, TResult](wrapped=func, factory=factory)

    return decorator
