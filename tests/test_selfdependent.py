from typing import Annotated, AsyncGenerator, Generator, cast

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fasted import selfdependent


def make_foo(base_1: float, base_2: float) -> "Foo":
    """FastAPI dependency that produces a `Foo` instance."""
    return Foo(base_1 + base_2)


class BaseFoo:
    def __init__(self, base: float) -> None:
        self._base = base

    def sync_method(self, mul: float | None = None) -> float:
        return self._base if mul is None else (self._base * mul)


class Foo(BaseFoo):  # Test inheritence and super() support.
    @selfdependent(make_foo)
    def factory(self, mul: float | None = None) -> float:
        return self._base if mul is None else (self._base * mul)

    @selfdependent()
    def sync_method(self, mul: float | None = None) -> float:
        return super().sync_method(mul)

    @selfdependent()
    async def async_method(self, mul: float | None = None) -> float:
        return self._base if mul is None else (self._base * mul)

    @selfdependent()
    def sync_generator(self, exp: float) -> Generator[float, None, None]:
        yield cast(float, self._base**exp)

    @selfdependent()
    async def async_generator(self, exp: float) -> AsyncGenerator[float, None]:
        yield cast(float, self._base**exp)


@pytest.fixture(scope="module")
def app() -> FastAPI:
    app = FastAPI()

    DependsFactory = Annotated[float, Depends(Foo.factory)]
    DependsSyncMethod = Annotated[float, Depends(Foo.sync_method)]
    DependsAsyncMethod = Annotated[float, Depends(Foo.async_method)]
    DependsSyncGenerator = Annotated[float, Depends(Foo.sync_generator)]
    DependsAsyncGenerator = Annotated[float, Depends(Foo.async_generator)]

    @app.get("/manual")
    async def manual() -> float:
        foo = Foo(3)

        # Validate that there are no mypy errors and every method behaves as expected.
        result = await foo.async_method()

        assert foo.sync_method() == result
        assert result**2 == next(foo.sync_generator(2))
        assert result**2 == await anext(foo.async_generator(2))

        return result

    @app.get("/factory")
    def factory(value: DependsFactory) -> float:
        return value

    @app.get("/sync-method")
    def sync_method(value: DependsSyncMethod) -> float:
        return value

    @app.get("/async-method")
    async def async_method(value: DependsAsyncMethod) -> float:
        return value

    @app.get("/sync-generator")
    async def sync_generator(value: DependsSyncGenerator) -> float:
        return value

    @app.get("/async-generator")
    async def async_generator(value: DependsAsyncGenerator) -> float:
        return value

    return app


@pytest.fixture(scope="module")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


def test_manual(client: TestClient) -> None:
    response = client.get("/manual")
    response.raise_for_status()
    assert float(response.text) == 3


@pytest.mark.parametrize(
    ("params", "expected"),
    (
        ({"base_1": 2, "base_2": 4}, 6),
        ({"base_1": 2, "base_2": 4, "mul": 7}, 42),
    ),
)
def test_factory(client: TestClient, params: dict[str, float], expected: float) -> None:
    response = client.get("/factory", params=params)
    response.raise_for_status()
    assert float(response.text) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    (
        ({"base": 6}, 6),
        ({"base": 6, "mul": 7}, 42),
    ),
)
def test_sync_method(client: TestClient, params: dict[str, float], expected: float) -> None:
    response = client.get("/sync-method", params=params)
    response.raise_for_status()
    assert float(response.text) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    (
        ({"base": 6}, 6),
        ({"base": 6, "mul": 7}, 42),
    ),
)
def test_async_method(client: TestClient, params: dict[str, float], expected: float) -> None:
    response = client.get("/async-method", params=params)
    response.raise_for_status()
    assert float(response.text) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    (({"base": 3, "exp": 3}, 27),),
)
def test_sync_generator(client: TestClient, params: dict[str, float], expected: float) -> None:
    response = client.get("/sync-generator", params=params)
    response.raise_for_status()
    assert float(response.text) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    (({"base": 3, "exp": 3}, 27),),
)
def test_async_generator(client: TestClient, params: dict[str, float], expected: float) -> None:
    response = client.get("/async-generator", params=params)
    response.raise_for_status()
    assert float(response.text) == expected
