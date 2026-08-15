from collections.abc import Callable

eventQueue: object

def queueFunction(
	queue: object,
	func: Callable[..., object],
	*args: object,
	**kwargs: object,
) -> None: ...
