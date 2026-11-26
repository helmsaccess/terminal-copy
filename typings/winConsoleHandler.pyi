from textInfos import TextInfo

class _Size:
	x: int

class _Window:
	Left: int
	Top: int
	Right: int
	Bottom: int

class _Buffer:
	dwSize: _Size
	srWindow: _Window

class WinConsoleTextInfo(TextInfo):
	consoleScreenBufferInfo: _Buffer
	clipboardText: str
	def __init__(self, obj: object, position: str) -> None: ...
