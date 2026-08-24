"""Uniquely named app module providing review-cursor copying in Windows Terminal."""

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
from utils.security import objectBelowLockScreenAndWindowsIsLocked

# Preserve another add-on's direct Windows Terminal AppModule instead of competing for its module name.
if TYPE_CHECKING:
	from appModules.windowsterminal import AppModule as BaseAppModule
else:
	try:
		from appModules.windowsterminal import AppModule as BaseAppModule
	except ModuleNotFoundError as error:
		if error.name != "appModules.windowsterminal":
			raise
		BaseAppModule = appModuleHandler.AppModule

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


class AppModule(BaseAppModule):
	"""Add review-cursor region copying to Windows Terminal."""

	def __init__(self, processID: int, appName: str | None = None) -> None:
		super().__init__(processID, appName)
		self._selection = SelectionController()
		self._copyThread: threading.Thread | None = None
		self._isTerminating = False

	@override
	def terminate(self) -> None:
		"""Release saved UIA ranges when Windows Terminal exits or the add-on reloads."""
		self._isTerminating = True
		self._selection.clear()
		super().terminate()

	def _getReviewTextInfo(self) -> UIATextInfo | None:
		"""Return the current review position when it is Windows Terminal UIA text."""
		try:
			info = api.getReviewPosition()
			obj = info.obj
			if objectBelowLockScreenAndWindowsIsLocked(obj):
				return None
			if getattr(obj, "appModule", None) is not self:
				return None
			if not isinstance(info, UIATextInfo):
				return None
			if getattr(obj, "UIATextPattern", None) is None:
				return None
			return info
		except (AttributeError, LookupError, RuntimeError):
			return None

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
			# Translators: Announced when the review cursor is not in Windows Terminal's UIA text.
			ui.message(_("Move the review cursor to Windows Terminal text first"))
			return
		try:
			result = self._selection.addMark(info)
		except DifferentTextContainerError:
			# Translators: Announced when region marks are placed in different terminal tabs or buffers.
			ui.message(_("Both marks must be in the same terminal buffer"))
			return
		if result is MarkResult.START_SET:
			# Translators: Announced after the first Terminal Copy region mark is set.
			ui.message(_("Start mark set"))
		else:
			# Translators: Announced after the second Terminal Copy region mark is set.
			ui.message(_("End mark set"))

	@script(
		# Translators: Description of the command that copies the marked Windows Terminal region.
		description=_("Copy the marked Windows Terminal region"),
		gesture="kb:NVDA+c",
		category=SCRIPT_CATEGORY,
	)
	def script_copyRegion(self, gesture: inputCore.InputGesture) -> None:
		"""Copy the selected UIA text without blocking NVDA's main thread."""
		if self._copyThread is not None and self._copyThread.is_alive():
			# Translators: Announced when another Terminal Copy operation is still running.
			ui.message(_("A copy operation is already in progress"))
			return
		try:
			selection = self._selection.buildRange()
		except IncompleteSelectionError:
			# Translators: Announced when copy is requested before both region marks are set.
			ui.message(_("Set start and end marks first"))
			return
		except Exception as error:
			log.error("Terminal Copy could not construct the selected range (%s)", type(error).__name__)
			# Translators: Announced when saved UIA ranges are no longer valid.
			ui.message(_("The marked region is no longer available"))
			return
		if objectBelowLockScreenAndWindowsIsLocked(selection.obj):
			# Translators: Announced when a saved region cannot be accessed from the Windows lock screen.
			ui.message(_("The marked region is no longer available"))
			return
		self._copyThread = threading.Thread(
			target=self._copyInBackground,
			args=(selection,),
			name="TerminalCopy.UIACopy",
			daemon=True,
		)
		self._copyThread.start()
		# Translators: Announced while a potentially large terminal region is copied.
		ui.message(_("Copying marked region"))

	def _copyInBackground(self, selection: TextRange) -> None:
		"""Retrieve UIA text and copy it from a COM MTA worker thread."""
		hasCopied = False
		errorName: str | None = None
		isComInitialized = False
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
			isComInitialized = True
			text = normalizeTerminalText(selection.text)
			if text:
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
