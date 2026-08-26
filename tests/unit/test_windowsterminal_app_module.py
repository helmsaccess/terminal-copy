"""Integration tests for Terminal Copy's Windows Terminal app module."""

import builtins
import importlib
import inspect
import logging
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest import mock


class FakeBaseAppModule:
	"""Minimal stand-in for NVDA's AppModule base class."""

	def __init__(self, processID: int, appName: str | None = None) -> None:
		self.processID = processID
		self.appName = appName or "windowsterminal"
		self.hasTerminated = False

	def terminate(self) -> None:
		self.hasTerminated = True


class FakeCompanionAppModule(FakeBaseAppModule):
	"""Stand in for an unrelated add-on's direct Windows Terminal app module."""

	def __init__(self, processID: int, appName: str | None = None) -> None:
		super().__init__(processID, appName)
		self.companionEvents: list[str] = []

	def script_companionCommand(self, gesture: object) -> None:
		self.companionEvents.append("script")

	def event_gainFocus(self, obj: object, nextHandler) -> None:
		self.companionEvents.append("event")
		nextHandler()

	def chooseNVDAObjectOverlayClasses(self, obj: object, clsList: list[type]) -> None:
		self.companionEvents.append("overlay")
		clsList.append(FakeUIATextInfo)

	def terminate(self) -> None:
		self.companionEvents.append("terminate")
		super().terminate()


class FakeUIATextInfo:
	"""Offset range accepted as UIA text by the app module."""

	def __init__(self, document: str, start: int, obj: object, end: int | None = None) -> None:
		self.document = document
		self.start = start
		self.end = start if end is None else end
		self.obj = obj

	@property
	def text(self) -> str:
		return self.document[self.start : self.end]

	def copy(self) -> "FakeUIATextInfo":
		return FakeUIATextInfo(self.document, self.start, self.obj, self.end)

	def collapse(self, end: bool = False) -> None:
		if end:
			self.start = self.end
		else:
			self.end = self.start

	def compareEndPoints(self, other: "FakeUIATextInfo", which: str) -> int:
		ownName, otherName = which.split("To")
		ownValue = self.start if ownName == "start" else self.end
		otherValue = other.start if otherName == "Start" else other.end
		return (ownValue > otherValue) - (ownValue < otherValue)

	def setEndPoint(self, other: "FakeUIATextInfo", which: str) -> None:
		ownName, otherName = which.split("To")
		otherValue = other.start if otherName == "Start" else other.end
		if ownName == "start":
			self.start = otherValue
		else:
			self.end = otherValue

	def expand(self, unit: str) -> None:
		if unit != "character":
			raise ValueError(unit)
		self.end = min(self.start + 1, len(self.document))


class ImmediateThread:
	"""Run a thread target synchronously for deterministic tests."""

	def __init__(self, *, target, args, name: str, daemon: bool) -> None:
		self._target = target
		self._args = args
		self.name = name
		self.daemon = daemon
		self._isAlive = False

	def start(self) -> None:
		self._isAlive = True
		try:
			self._target(*self._args)
		finally:
			self._isAlive = False

	def is_alive(self) -> bool:
		return self._isAlive


class TestWindowsTerminalAppModule(unittest.TestCase):
	"""Exercise the user-facing mark and copy workflow with mocked NVDA APIs."""

	@classmethod
	def setUpClass(cls) -> None:
		cls._originalTranslation = getattr(builtins, "_", None)
		builtins._ = lambda message: message
		cls._addonPath = str(Path(__file__).parents[2] / "addon")
		sys.path.insert(0, cls._addonPath)

		addonHandler = ModuleType("addonHandler")
		translations = {
			"End mark set": "Endmarke gesetzt",
			"Start mark set": "Anfangsmarke gesetzt",
		}

		def initTranslation() -> None:
			callerFrame = inspect.currentframe().f_back
			try:
				callerModule = inspect.getmodule(callerFrame)
				callerModule._ = lambda message: translations.get(message, message)
			finally:
				del callerFrame

		addonHandler.initTranslation = initTranslation
		cls.api = ModuleType("api")
		appModuleHandler = ModuleType("appModuleHandler")
		appModuleHandler.AppModule = FakeBaseAppModule
		comtypes = ModuleType("comtypes")
		comtypes.COINIT_MULTITHREADED = 0
		comtypes.CoInitializeEx = lambda flags: None
		comtypes.CoUninitialize = lambda: None
		inputCore = ModuleType("inputCore")
		inputCore.InputGesture = object
		logHandler = ModuleType("logHandler")
		logHandler.log = logging.getLogger("terminalCopyTest")
		nvdaObjects = ModuleType("NVDAObjects")
		nvdaObjects.__path__ = []
		nvdaObjectsUIA = ModuleType("NVDAObjects.UIA")
		nvdaObjectsUIA.UIATextInfo = FakeUIATextInfo
		cls.queueHandler = ModuleType("queueHandler")
		cls.queueHandler.eventQueue = object()
		cls.queueHandler.queueFunction = lambda queue, function, *args: function(*args)
		scriptHandler = ModuleType("scriptHandler")
		scriptHandler.script = lambda **kwargs: lambda function: function
		cls.ui = ModuleType("ui")
		utils = ModuleType("utils")
		utils.__path__ = []
		security = ModuleType("utils.security")
		security.isLocked = False
		security.objectBelowLockScreenAndWindowsIsLocked = lambda obj: security.isLocked
		cls.security = security
		cls._stubNames = {
			"addonHandler": addonHandler,
			"api": cls.api,
			"appModuleHandler": appModuleHandler,
			"comtypes": comtypes,
			"inputCore": inputCore,
			"logHandler": logHandler,
			"NVDAObjects": nvdaObjects,
			"NVDAObjects.UIA": nvdaObjectsUIA,
			"queueHandler": cls.queueHandler,
			"scriptHandler": scriptHandler,
			"ui": cls.ui,
			"utils": utils,
			"utils.security": security,
		}
		cls._originalModules = {name: sys.modules.get(name) for name in cls._stubNames}
		sys.modules.update(cls._stubNames)
		cls.moduleName = "appModules.terminalCopyWindowsterminal"
		cls.module = importlib.import_module(cls.moduleName)
		cls.module.threading.Thread = ImmediateThread

	@classmethod
	def tearDownClass(cls) -> None:
		sys.modules.pop(cls.moduleName, None)
		for name, original in cls._originalModules.items():
			if original is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = original
		sys.path.remove(cls._addonPath)
		if cls._originalTranslation is None:
			delattr(builtins, "_")
		else:
			builtins._ = cls._originalTranslation

	def setUp(self) -> None:
		self.messages: list[str] = []
		self.copiedText: list[str] = []
		self.ui.message = self.messages.append
		self.api.copyToClip = self.copyToClip
		self.security.isLocked = False
		self.appModule = self.module.AppModule(42, "windowsterminal")
		self.owner = type(
			"TerminalOwner",
			(),
			{"appModule": self.appModule, "UIATextPattern": object()},
		)()

	def copyToClip(self, text: str, notify: bool = False) -> bool:
		self.copiedText.append(text)
		return True

	def setReviewPosition(self, offset: int) -> None:
		info = FakeUIATextInfo("abcdef", offset, self.owner)
		self.api.getReviewPosition = lambda: info

	def testTwoMarksCopyInclusiveUIARange(self) -> None:
		"""The full user workflow copies both marked characters."""
		self.setReviewPosition(1)
		self.appModule.script_toggleRegionMark(object())
		self.setReviewPosition(3)
		self.appModule.script_toggleRegionMark(object())
		self.appModule.script_copyRegion(object())
		self.assertEqual(self.copiedText, ["bcd"])
		self.assertIn("Marked region copied", self.messages)

	def testUsesNVDAAppModuleBaseWithoutCompanion(self) -> None:
		"""Terminal Copy remains active when no direct Windows Terminal app module exists."""
		self.assertIs(self.module.BaseAppModule, FakeBaseAppModule)
		self.assertIsInstance(self.appModule, FakeBaseAppModule)

	def testComposesWithDirectCompanionAppModule(self) -> None:
		"""A direct app module keeps its scripts, events, overlays, and lifecycle."""
		companionModule = ModuleType("appModules.windowsterminal")
		companionModule.AppModule = FakeCompanionAppModule
		originalModule = sys.modules.pop(self.moduleName)
		try:
			with mock.patch.dict(sys.modules, {"appModules.windowsterminal": companionModule}):
				compatibleModule = importlib.import_module(self.moduleName)
				compatibleModule.threading.Thread = ImmediateThread
				compatibleAppModule = compatibleModule.AppModule(42, "windowsterminal")
				self.assertIs(compatibleModule.BaseAppModule, FakeCompanionAppModule)
				self.assertIsInstance(compatibleAppModule, FakeCompanionAppModule)
				owner = type(
					"CompatibleTerminalOwner",
					(),
					{"appModule": compatibleAppModule, "UIATextPattern": object()},
				)()
				self.api.getReviewPosition = lambda: FakeUIATextInfo("abcdef", 1, owner)
				compatibleAppModule.script_toggleRegionMark(object())
				self.api.getReviewPosition = lambda: FakeUIATextInfo("abcdef", 3, owner)
				compatibleAppModule.script_toggleRegionMark(object())
				compatibleAppModule.script_copyRegion(object())
				compatibleAppModule.script_companionCommand(object())
				hasCalledNextHandler = False

				def nextHandler() -> None:
					nonlocal hasCalledNextHandler
					hasCalledNextHandler = True

				compatibleAppModule.event_gainFocus(object(), nextHandler)
				overlays: list[type] = []
				compatibleAppModule.chooseNVDAObjectOverlayClasses(object(), overlays)
				compatibleAppModule.terminate()
				self.assertTrue(hasCalledNextHandler)
				self.assertEqual(self.copiedText, ["bcd"])
				self.assertEqual(overlays, [FakeUIATextInfo])
				self.assertEqual(
					compatibleAppModule.companionEvents,
					["script", "event", "overlay", "terminate"],
				)
				self.assertTrue(compatibleAppModule.hasTerminated)
		finally:
			sys.modules.pop(self.moduleName, None)
			sys.modules[self.moduleName] = originalModule

	def testDoesNotHideCompanionImportFailure(self) -> None:
		"""A missing dependency inside a companion module remains visible to NVDA."""
		originalImport = builtins.__import__
		originalModule = sys.modules.pop(self.moduleName)

		def guardedImport(name, globals=None, locals=None, fromlist=(), level=0):
			if name == "appModules.windowsterminal":
				raise ModuleNotFoundError(
					"Companion dependency is missing",
					name="companionDependency",
				)
			return originalImport(name, globals, locals, fromlist, level)

		try:
			with mock.patch.object(builtins, "__import__", guardedImport):
				with self.assertRaisesRegex(ModuleNotFoundError, "Companion dependency is missing") as caught:
					importlib.import_module(self.moduleName)
			self.assertEqual(caught.exception.name, "companionDependency")
		finally:
			sys.modules.pop(self.moduleName, None)
			sys.modules[self.moduleName] = originalModule

	def testMarkAnnouncementsUseAddonTranslation(self) -> None:
		"""Mark announcements use the add-on catalog rather than NVDA's core catalog."""
		self.setReviewPosition(1)
		self.appModule.script_toggleRegionMark(object())
		self.setReviewPosition(3)
		self.appModule.script_toggleRegionMark(object())
		self.assertEqual(self.messages, ["Anfangsmarke gesetzt", "Endmarke gesetzt"])

	def testCopyCollapsesWhitespaceOnlyLines(self) -> None:
		"""Whitespace-only lines are copied as blank lines without losing their breaks."""
		document = "first\r\n \t\r\nlast"
		self.api.getReviewPosition = lambda: FakeUIATextInfo(document, 0, self.owner)
		self.appModule.script_toggleRegionMark(object())
		self.api.getReviewPosition = lambda: FakeUIATextInfo(document, len(document) - 1, self.owner)
		self.appModule.script_toggleRegionMark(object())
		self.appModule.script_copyRegion(object())
		self.assertEqual(self.copiedText, ["first\r\n\r\nlast"])

	def testCopyRemovesOuterWhitespaceOnlyLines(self) -> None:
		"""Whitespace-only lines surrounding terminal content are not copied."""
		document = " \r\nfirst\r\nlast\r\n\t"
		self.api.getReviewPosition = lambda: FakeUIATextInfo(document, 0, self.owner)
		self.appModule.script_toggleRegionMark(object())
		self.api.getReviewPosition = lambda: FakeUIATextInfo(document, len(document) - 1, self.owner)
		self.appModule.script_toggleRegionMark(object())
		self.appModule.script_copyRegion(object())
		self.assertEqual(self.copiedText, ["first\r\nlast"])

	def testCopyRemovesTrailingWhitespaceFromTextLines(self) -> None:
		"""Trailing spaces and tabs are removed while indentation remains."""
		document = "  first \t\r\nsecond  "
		self.api.getReviewPosition = lambda: FakeUIATextInfo(document, 0, self.owner)
		self.appModule.script_toggleRegionMark(object())
		self.api.getReviewPosition = lambda: FakeUIATextInfo(document, len(document) - 1, self.owner)
		self.appModule.script_toggleRegionMark(object())
		self.appModule.script_copyRegion(object())
		self.assertEqual(self.copiedText, ["  first\r\nsecond"])

	def testThirdMarkPressClearsCompletedRegion(self) -> None:
		"""The third NVDA+R press resets the two-mark state."""
		self.setReviewPosition(1)
		self.appModule.script_toggleRegionMark(object())
		self.setReviewPosition(2)
		self.appModule.script_toggleRegionMark(object())
		self.appModule.script_toggleRegionMark(object())
		self.appModule.script_copyRegion(object())
		self.assertEqual(self.copiedText, [])
		self.assertEqual(self.messages[-1], "Set start and end marks first")

	def testCopyRejectsSavedRegionAfterWindowsLocks(self) -> None:
		"""A region marked before locking cannot expose terminal text afterward."""
		self.setReviewPosition(1)
		self.appModule.script_toggleRegionMark(object())
		self.setReviewPosition(3)
		self.appModule.script_toggleRegionMark(object())
		self.security.isLocked = True
		self.appModule.script_copyRegion(object())
		self.assertEqual(self.copiedText, [])
		self.assertEqual(self.messages[-1], "The marked region is no longer available")


if __name__ == "__main__":
	unittest.main()
