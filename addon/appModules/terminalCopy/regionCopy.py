"""Shared review-cursor copy commands for supported Windows terminals."""

import threading
from typing import TYPE_CHECKING, override

import addonHandler
import api
import appModuleHandler
import comtypes
import inputCore
from logHandler import log
from NVDAObjects.UIA import UIATextInfo
import queueHandler
from scriptHandler import script
import ui
from textInfos import TextInfo
from utils.security import objectBelowLockScreenAndWindowsIsLocked

from appModules.terminalCopy.selection import (
	DifferentTextContainerError,
	IncompleteSelectionError,
	MarkResult,
	normalizeTerminalText,
	SelectionController,
	TextRange,
)


addonHandler.initTranslation()
if TYPE_CHECKING:

	def _(message: str) -> str: ...


# Translators: Name of the section containing Terminal Copy commands in NVDA's Input Gestures dialog.
SCRIPT_CATEGORY = _("Terminal Copy")


class RegionCopyAppModule(appModuleHandler.AppModule):
	"""Provide scoped review-cursor region copying."""

	def __init__(self, processID: int, appName: str | None = None) -> None:
		super().__init__(processID, appName)
		self._selection = SelectionController()
		self._markContext: object = None
		self._copyThread: threading.Thread | None = None
		self._isTerminating = False

	@override
	def terminate(self) -> None:
		"""Release saved UIA ranges when the application exits or the add-on reloads."""
		self._isTerminating = True
		self._selection.clear()
		super().terminate()

	def _getReviewTextInfo(self) -> TextInfo | None:
		"""Return the current review position when it is supported terminal text."""
		try:
			info = api.getReviewPosition()
			obj = info.obj
			if objectBelowLockScreenAndWindowsIsLocked(obj):
				return None
			if getattr(obj, "appModule", None) is not self:
				return None
			if self._acceptsReviewText(info):
				return info
		except (AttributeError, LookupError, RuntimeError, comtypes.COMError):
			pass
		return None

	def _acceptsReviewText(self, info: TextInfo) -> bool:
		"""Accept UI Automation review ranges owned by the app module."""
		return isinstance(info, UIATextInfo) and getattr(info.obj, "UIATextPattern", None) is not None

	def _getMarkContext(self, info: TextInfo) -> object:
		"""Return any backend-specific context that must stay fixed between marks."""
		return None

	def _prepareCopy(self, selection: TextRange) -> TextRange | str:
		"""Prepare the selected text or a range which can be read in the worker."""
		return selection

	def _validateCopySource(self, firstMark: TextRange) -> None:
		"""Reject saved ranges before accessing a protected buffer."""
		if objectBelowLockScreenAndWindowsIsLocked(firstMark.obj):
			raise RuntimeError("Selection unavailable on the lock screen")

	@script(
		# Translators: Description of the command that marks a region using the review cursor.
		description=_("Set or clear a Terminal Copy region mark"),
		gesture="kb:NVDA+r",
		category=SCRIPT_CATEGORY,
	)
	def script_toggleRegionMark(self, gesture: inputCore.InputGesture) -> None:
		"""Set start/end marks, or clear a completed region on the third press."""
		if self._selection.isComplete:
			self._selection.clear()
			# Translators: Announced after both Terminal Copy region marks are cleared.
			ui.message(_("Region marks cleared"))
			return
		info = self._getReviewTextInfo()
		if info is None:
			# Translators: Announced when the review cursor is not in supported terminal text.
			ui.message(_("Move the review cursor to terminal text first"))
			return
		try:
			context = self._getMarkContext(info)
			if self._selection.hasStart and context != self._markContext:
				self._selection.clear()
			result = self._selection.addMark(info)
			self._markContext = context
		except DifferentTextContainerError:
			# Translators: Announced when region marks are placed in different terminal tabs or buffers.
			ui.message(_("Both marks must be in the same terminal buffer"))
			return
		except (AttributeError, LookupError, OSError, RuntimeError, comtypes.COMError):
			# Translators: Announced when a terminal position or selection becomes unavailable.
			ui.message(_("The marked region is no longer available"))
			return
		if result is MarkResult.START_SET:
			# Translators: Announced after the first Terminal Copy region mark is set.
			ui.message(_("Start mark set"))
		else:
			# Translators: Announced after the second Terminal Copy region mark is set.
			ui.message(_("End mark set"))

	@script(
		# Translators: Description of the command that copies the marked terminal region.
		description=_("Copy the marked terminal region"),
		gesture="kb:NVDA+c",
		category=SCRIPT_CATEGORY,
	)
	def script_copyRegion(self, gesture: inputCore.InputGesture) -> None:
		"""Copy the selected UIA text without blocking NVDA's main thread."""
		if self._copyThread is not None:
			# Translators: Announced when another Terminal Copy operation is still running.
			ui.message(_("A copy operation is already in progress"))
			return
		try:
			selection = self._selection.buildRange(self._validateCopySource)
			source = self._prepareCopy(selection)
		except IncompleteSelectionError:
			# Translators: Announced when copy is requested before both region marks are set.
			ui.message(_("Set start and end marks first"))
			return
		except Exception as error:
			log.error("Terminal Copy could not construct the selected range (%s)", type(error).__name__)
			# Translators: Announced when saved UIA ranges are no longer valid.
			ui.message(_("The marked region is no longer available"))
			return
		self._copyThread = threading.Thread(
			target=self._copyInBackground,
			args=(source,),
			name="TerminalCopy.Copy",
			daemon=True,
		)
		self._copyThread.start()
		# Translators: Announced while a potentially large terminal region is copied.
		ui.message(_("Copying marked region"))

	def _copyInBackground(self, source: TextRange | str) -> None:
		"""Read UIA when needed and normalize and copy text in a worker."""
		hasCopied = False
		errorName: str | None = None
		isComInitialized = False
		try:
			if not isinstance(source, str):
				comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
				isComInitialized = True
				source = source.text
			text = normalizeTerminalText(source)
			if text and not self._isTerminating:
				hasCopied = api.copyToClip(text, notify=False)
		except Exception as error:
			errorName = type(error).__name__
		finally:
			if isComInitialized:
				comtypes.CoUninitialize()
		queueHandler.queueFunction(
			queueHandler.eventQueue,
			self._finishCopy,
			hasCopied,
			errorName,
		)

	def _finishCopy(self, hasCopied: bool, errorName: str | None) -> None:
		"""Report a completed copy operation on NVDA's main thread."""
		self._copyThread = None
		if self._isTerminating:
			return
		if errorName is not None:
			log.error("Terminal Copy failed while reading or copying the selected range (%s)", errorName)
		if hasCopied:
			# Translators: Announced after the marked terminal region is copied successfully.
			ui.message(_("Marked region copied"))
		else:
			# Translators: Announced when the marked terminal region could not be copied.
			ui.message(_("Unable to copy the marked region"))
