"""Tests for Terminal Copy's review-cursor selection logic."""

import unittest

from addon.appModules.terminalCopy.selection import (
	DifferentTextContainerError,
	IncompleteSelectionError,
	MarkResult,
	normalizeTerminalText,
	SelectionController,
)


class TestTerminalTextNormalization(unittest.TestCase):
	"""Verify whitespace cleanup without changing text or line endings."""

	def testWhitespaceOnlyLinesBecomeEmpty(self) -> None:
		"""Spaces and tabs are removed when they are the line's only content."""
		self.assertEqual("first\n\n\nlast", normalizeTerminalText("first\n  \n\t\nlast"))

	def testLineEndingsArePreserved(self) -> None:
		"""CRLF, LF, and CR line endings remain byte-for-byte unchanged."""
		text = "first\r\n \t\r\nsecond\n  \nthird\r\t\rfourth"
		self.assertEqual("first\r\n\r\nsecond\n\nthird\r\rfourth", normalizeTerminalText(text))

	def testTrailingWhitespaceIsRemovedAndIndentationIsPreserved(self) -> None:
		"""Visible lines lose trailing whitespace without losing indentation."""
		text = "  indented  \ntext\t\n"
		self.assertEqual("  indented\ntext\n", normalizeTerminalText(text))

	def testFinalWhitespaceOnlyLineWithoutEndingBecomesEmpty(self) -> None:
		"""A final whitespace-only line is removed even without a terminator."""
		self.assertEqual("first", normalizeTerminalText("first\n  "))

	def testLeadingAndTrailingWhitespaceOnlyLinesAreRemoved(self) -> None:
		"""Outer blank lines and their separators are omitted from copied text."""
		text = " \t\r\n\r\nfirst\r\n \t\r\nlast\r\n\t\r\n"
		self.assertEqual("first\r\n\r\nlast", normalizeTerminalText(text))

	def testWhitespaceOnlySelectionBecomesEmpty(self) -> None:
		"""A selection without visible text has no lines left to copy."""
		self.assertEqual("", normalizeTerminalText(" \r\n\t\n"))


class FakeTextRange:
	"""Small offset-based implementation of the TextRange protocol."""

	def __init__(self, document: str, start: int, end: int, obj: object) -> None:
		self.document = document
		self.start = start
		self.end = end
		self.obj = obj

	@property
	def text(self) -> str:
		"""Return the represented text."""
		return self.document[self.start : self.end]

	def copy(self) -> "FakeTextRange":
		"""Return an independent range."""
		return FakeTextRange(self.document, self.start, self.end, self.obj)

	def collapse(self, end: bool = False) -> None:
		"""Collapse to the requested endpoint."""
		if end:
			self.start = self.end
		else:
			self.end = self.start

	def compareEndPoints(self, other: "FakeTextRange", which: str) -> int:
		"""Compare endpoints using NVDA's endpoint naming convention."""
		ownName, otherName = which.split("To")
		ownValue = self.start if ownName == "start" else self.end
		otherValue = other.start if otherName == "Start" else other.end
		return (ownValue > otherValue) - (ownValue < otherValue)

	def setEndPoint(self, other: "FakeTextRange", which: str) -> None:
		"""Set an endpoint using NVDA's endpoint naming convention."""
		ownName, otherName = which.split("To")
		otherValue = other.start if otherName == "Start" else other.end
		if ownName == "start":
			self.start = otherValue
		else:
			self.end = otherValue

	def expand(self, unit: str) -> None:
		"""Expand a collapsed range to one character."""
		if unit != "character":
			raise ValueError(unit)
		self.end = min(self.start + 1, len(self.document))


class EquivalentOwner:
	"""Represent recreated wrappers for the same underlying UIA element."""

	def __init__(self, identity: int) -> None:
		self.identity = identity

	def __eq__(self, other: object) -> bool:
		return isinstance(other, EquivalentOwner) and self.identity == other.identity


class TestSelectionController(unittest.TestCase):
	"""Verify ordering, ownership, inclusion, and reset behavior."""

	def setUp(self) -> None:
		self.document = "abcdef"
		self.owner = object()
		self.controller = SelectionController()

	def makeRange(self, start: int, end: int | None = None, owner: object | None = None) -> FakeTextRange:
		"""Create a fake range in the shared document."""
		return FakeTextRange(
			self.document,
			start,
			start if end is None else end,
			self.owner if owner is None else owner,
		)

	def testForwardSelectionIncludesBothMarkedCharacters(self) -> None:
		"""The character under the end mark is included."""
		self.assertIs(self.controller.addMark(self.makeRange(1)), MarkResult.START_SET)
		self.assertIs(self.controller.addMark(self.makeRange(3)), MarkResult.END_SET)
		self.assertEqual(self.controller.buildRange().text, "bcd")

	def testReverseSelectionIsNormalizedAndInclusive(self) -> None:
		"""Marks can be set from bottom to top without producing an empty range."""
		self.controller.addMark(self.makeRange(4))
		self.controller.addMark(self.makeRange(1))
		self.assertEqual(self.controller.buildRange().text, "bcde")

	def testSamePositionCopiesOneCharacter(self) -> None:
		"""Two marks on one position copy the current character."""
		self.controller.addMark(self.makeRange(2))
		self.controller.addMark(self.makeRange(2))
		self.assertEqual(self.controller.buildRange().text, "c")

	def testStoredMarkIsCollapsedCopy(self) -> None:
		"""Changing an original review range does not change its saved mark."""
		original = self.makeRange(1, 5)
		self.controller.addMark(original)
		original.start = 0
		self.controller.addMark(self.makeRange(2))
		self.assertEqual(self.controller.buildRange().text, "bc")

	def testDifferentTerminalBuffersAreRejected(self) -> None:
		"""A range cannot cross terminal tabs or UIA text containers."""
		self.controller.addMark(self.makeRange(1))
		with self.assertRaises(DifferentTextContainerError):
			self.controller.addMark(self.makeRange(3, owner=object()))
		self.assertFalse(self.controller.isComplete)

	def testEquivalentTextContainerWrappersAreAccepted(self) -> None:
		"""A recreated NVDA wrapper for the same UIA element remains compatible."""
		firstOwner = EquivalentOwner(1)
		secondOwner = EquivalentOwner(1)
		self.controller.addMark(self.makeRange(1, owner=firstOwner))
		self.controller.addMark(self.makeRange(3, owner=secondOwner))
		self.assertEqual(self.controller.buildRange().text, "bcd")

	def testIncompleteSelectionCannotBuildRange(self) -> None:
		"""Both marks are required before copying."""
		self.controller.addMark(self.makeRange(1))
		with self.assertRaises(IncompleteSelectionError):
			self.controller.buildRange()

	def testClearReleasesSelectionState(self) -> None:
		"""Clearing a complete selection permits a new start mark."""
		self.controller.addMark(self.makeRange(1))
		self.controller.addMark(self.makeRange(2))
		self.controller.clear()
		self.assertFalse(self.controller.isComplete)
		self.assertIs(self.controller.addMark(self.makeRange(4)), MarkResult.START_SET)


if __name__ == "__main__":
	unittest.main()
