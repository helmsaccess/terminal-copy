from collections.abc import Callable
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")

def script(
	*,
	description: str | None = None,
	gesture: str | None = None,
	category: str | None = None,
	**kwargs: object,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...
