![Tests](https://github.com/volfpeter/fasted/actions/workflows/tests.yml/badge.svg)
![Linters](https://github.com/volfpeter/fasted/actions/workflows/linters.yml/badge.svg)
![Documentation](https://github.com/volfpeter/fasted/actions/workflows/build-docs.yml/badge.svg)
![PyPI package](https://img.shields.io/pypi/v/fasted?color=%2334D058&label=PyPI%20Package)

**Source code**: [https://github.com/volfpeter/fasted](https://github.com/volfpeter/fasted)

**Documentation and examples**: [https://volfpeter.github.io/fasted](https://volfpeter.github.io/fasted/)

# FastED

FastAPI dependencies and utilities.

## Installation

The package is available on PyPI and can be installed with:

```console
$ pip install fasted
```

## Features

### `selfdependent`

Decorator that let's you use your business objects' instance methods as FastAPI dependencies without writing any additional code.

Supports:

- **Sync and async** instance **methods**.
- **Sync and async generator** methods.
- An **optional factory** (FastAPI dependency) for creating the `self` instance. If not set, the class' `__init__()` method will serve as the dependency for creating the `self` instance.
- **Decorated** instance **methods will behave as expected** if called directly.

Example use:

```python
from typing import Annotated

from fastapi import FastAPI, Depends
from fasted import selfdependent


def double() -> "Multiplier":
    # Dependency that returns a Multiplier with base = 2.
    return Multiplier(2)


class Multiplier:
    def __init__(self, base: float) -> None:
        self.base = base

    @selfdependent()
    def multiply(self, mul: float) -> float:
        # `__init__()` will be used as the dependency to create `self`, so the route
        # where this method is used will have a `base` and a `mul` query parameter.
        return self.base * mul

    @selfdependent(double)
    async def double(self, mul: float) -> float:
        # `double()` will be used as the dependency to create `self`, so the route
        # where this method is used will only have a `mul` query parameter.
        return self.base * mul


app = FastAPI()


@app.get("/multiply")
def multiply_route(value: Annotated[float, Depends(Multiplier.multiply)]) -> float:
    # FastAPI will create the `Multiplier` instance based on `Multiplier.__init__()` and
    # automatically feed this `instance` as `self` to `Multiplier.multiply()` to calculate
    # the value of the dependency.
    return value


@app.get("/double")
def double_route(value: Annotated[float, Depends(Multiplier.double)]) -> float:
    # FastAPI will create the `Multiplier` instance using the `double()` factory (dependency)
    # and automatically feed this instance as `self` to `Multiplier.multiply()` to
    # calculate the value of the dependency.
    return value
```

### `Dependency`

Generic type for FastAPI dependencies.

Example use:

```python
from typing import Annotated, Generator

from fastapi import FastAPI, APIRouter
from fasted import Dependency
# from x import Session


def make_api(make_session: Dependency[Session]) -> APIRouter:
    DependsSession = Annotated[Session, Depends(make_session)]

    api = APIRouter()

    @api.get("/")
    def get(session: DependsSession) -> int:
        return 4

    return api


def make_db_session() -> Generator[Session, None, None]:
    with Session(database) as session:
        yield session


app = FastAPI()
app.include_router(make_api(make_db_session), prefix="/random-number")
```

## Dependencies

Being a FastAPI utility library, the only dependency is (and will remain) `fastapi`.

## Development

Use `ruff` for linting and formatting, `mypy` for static code analysis, and `pytest` for testing.

The documentation is built with `mkdocs-material` and `mkdocstrings`.

## Contributing

All contributions are welcome.

## License - MIT

The package is open-sourced under the conditions of the [MIT license](https://choosealicense.com/licenses/mit/).
