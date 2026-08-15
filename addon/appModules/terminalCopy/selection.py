"""Build a stable text range from two NVDA review positions."""

from enum import Enum, auto
from typing import Protocol, Self


class TextRange(Protocol):
	"""The subset of NVDA's ``TextInfo`` API used for selections."""

	@property
	def obj(self) -> object:
		"""Return the text container that owns this range."""
		...

	@property
	def text(self) -> str:
		"""Return the text represented by this range."""
		...

	def copy(self) -> Self:
		"""Return an independent copy of this range."""
		...

	def collapse(self, end: bool = False) -> None:
		"""Collapse this range to one endpoint."""
		...

	def compareEndPoints(self, other: Self, which: str) -> int:
		"""Compare one endpoint with an endpoint from another range."""
		...

	def setEndPoint(self, other: Self, which: str) -> None:
		"""Move one endpoint to an endpoint from another range."""
		...

	def expand(self, unit: str) -> None:
		"""Expand this range to the requested text unit."""
		...


class MarkResult(Enum):
	"""The result of adding a selection mark."""

	START_SET = auto()
	END_SET = auto()


class SelectionError(Exception):
	"""Base exception for invalid selection state."""


class IncompleteSelectionError(SelectionError):
	"""Raised when a selection does not have two marks."""


class DifferentTextContainerError(SelectionError):
	"""Raised when the marks belong to different text containers."""


def normalizeTerminalText(text: str) -> str:
	"""Trim outer blank lines and collapse whitespace-only lines inside the text."""
	lines: list[tuple[str, str]] = []
	for line in text.splitlines(keepends=True):
		if line.endswith("\r\n"):
			content, lineEnding = line[:-2], "\r\n"
		elif line.endswith(("\r", "\n")):
			content, lineEnding = line[:-1], line[-1]
		else:
			content, lineEnding = line, ""
		lines.append((content, lineEnding))
	firstContentLine = 0
	while firstContentLine < len(lines) and not lines[firstContentLine][0].strip():
		firstContentLine += 1
	lastContentLine = len(lines)
	while lastContentLine > firstContentLine and not lines[lastContentLine - 1][0].strip():
		lastContentLine -= 1
	if firstContentLine == lastContentLine:
		return ""
	hasTrailingBlankLines = lastContentLine < len(lines)
	result: list[str] = []
	for index, (content, lineEnding) in enumerate(lines[firstContentLine:lastContentLine]):
		content = content.rstrip()
		if hasTrailingBlankLines and index == lastContentLine - firstContentLine - 1:
			lineEnding = ""
		result.append(content + lineEnding)
	return "".join(result)


class SelectionController:
	"""Store two immutable review positions and construct an inclusive range."""

	def __init__(self) -> None:
		super().__init__()
		self._startMark: TextRange | None = None
		self._endMark: TextRange | None = None
		self._textContainer: object | None = None

	@property
	def isComplete(self) -> bool:
		"""Return whether both selection marks have been set."""
		return self._startMark is not None and self._endMark is not None

	def addMark(self, mark: TextRange) -> MarkResult:
		"""Store a collapsed copy of the next selection mark.

		:param mark: Current NVDA review position.
		:return: Which mark was stored.
		:raises DifferentTextContainerError: If the second mark belongs to another terminal buffer.
		"""
		storedMark = mark.copy()
		storedMark.collapse()
		if self._startMark is None:
			self._startMark = storedMark
			self._textContainer = mark.obj
			return MarkResult.START_SET
		if self._endMark is not None:
			raise RuntimeError("Selection is already complete")
		if not self._hasSameTextContainer(mark.obj):
			raise DifferentTextContainerError
		self._endMark = storedMark
		return MarkResult.END_SET

	def _hasSameTextContainer(self, textContainer: object) -> bool:
		"""Compare UIA-backed NVDA objects while tolerating a recreated Python wrapper."""
		if self._textContainer is None:
			return False
		if textContainer is self._textContainer:
			return True
		try:
			return textContainer == self._textContainer
		except Exception:
			return False

	def clear(self) -> None:
		"""Discard both marks and release their UIA text container."""
		self._startMark = None
		self._endMark = None
		self._textContainer = None

	def buildRange(self) -> TextRange:
		"""Create a forward, character-inclusive range between both marks.

		The stored UIA ranges are used directly. This deliberately avoids
		``POSITION_ALL``, which NVDA bounds to the visible Windows Terminal viewport.

		:return: A new range covering both marked characters.
		:raises IncompleteSelectionError: If either mark is missing.
		"""
		if self._startMark is None or self._endMark is None:
			raise IncompleteSelectionError
		start = self._startMark.copy()
		end = self._endMark.copy()
		start.collapse()
		end.collapse()
		if start.compareEndPoints(end, "startToStart") <= 0:
			selection, lastCharacter = start, end
		else:
			selection, lastCharacter = end, start
		lastCharacter.expand("character")
		selection.setEndPoint(lastCharacter, "endToEnd")
		return selection
