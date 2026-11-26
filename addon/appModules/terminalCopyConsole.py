"""Provide Terminal Copy commands in the classic Windows Console Host."""

from typing import override

import api
from textInfos import TextInfo
from winConsoleHandler import WinConsoleTextInfo

from appModules.terminalCopy.regionCopy import RegionCopyAppModule
from appModules.terminalCopy.selection import TextRange


class AppModule(RegionCopyAppModule):
	"""Use the active console's native UIA or legacy review range."""

	@override
	def _acceptsReviewText(self, info: TextInfo) -> bool:
		return (
			getattr(info.obj, "windowClassName", None) == "ConsoleWindowClass"
			and info.obj == api.getFocusObject()
			and (isinstance(info, WinConsoleTextInfo) or super()._acceptsReviewText(info))
		)

	@override
	def _getMarkContext(self, info: TextInfo) -> object:
		if isinstance(info, WinConsoleTextInfo):
			context = _viewport(info)
			if context != _viewport(WinConsoleTextInfo(info.obj, "first")):
				raise RuntimeError("The console viewport changed")
			return context
		return None

	@override
	def _validateCopySource(self, firstMark: TextRange) -> None:
		super()._validateCopySource(firstMark)
		if firstMark.obj != api.getFocusObject():
			raise RuntimeError("The marked console is no longer focused")
		if isinstance(firstMark, WinConsoleTextInfo):
			fresh = WinConsoleTextInfo(firstMark.obj, "first")
			if _viewport(fresh) != self._markContext:
				raise RuntimeError("The console viewport changed")

	@override
	def _prepareCopy(self, selection: TextRange) -> TextRange | str:
		if isinstance(selection, WinConsoleTextInfo):
			# NVDA's legacy backend uses a handle shared by the focused consoles.
			# Read the visible range on the main thread before another focus event can replace it.
			return selection.clipboardText
		return selection


def _viewport(info: WinConsoleTextInfo) -> tuple[int, int, int, int, int]:
	"""Identify the viewport that owns the legacy TextInfo's relative offsets."""
	buffer = info.consoleScreenBufferInfo
	window = buffer.srWindow
	return (buffer.dwSize.x, window.Left, window.Top, window.Right, window.Bottom)
