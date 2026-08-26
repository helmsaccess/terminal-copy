"""Tests for Terminal Copy's executable-to-app-module mapping."""

import importlib
from pathlib import Path
import sys
from types import ModuleType
import unittest


class FakeGlobalPlugin:
	"""Minimal global plugin base recording cooperative lifecycle calls."""

	lifecycle: list[str] = []

	def __init__(self) -> None:
		self.lifecycle.append("base initialized")

	def terminate(self) -> None:
		self.lifecycle.append("base terminated")


class TestGlobalPlugin(unittest.TestCase):
	"""Verify registration and cleanup of the Windows Terminal mapping."""

	@classmethod
	def setUpClass(cls) -> None:
		cls._addonPath = str(Path(__file__).parents[2] / "addon")
		sys.path.insert(0, cls._addonPath)
		cls.calls: list[tuple[str, ...]] = []
		appModuleHandler = ModuleType("appModuleHandler")
		appModuleHandler.registerExecutableWithAppModule = lambda executable, appModule: cls.calls.append(
			("register", executable, appModule),
		)
		appModuleHandler.unregisterExecutable = lambda executable: cls.calls.append(
			("unregister", executable),
		)
		globalPluginHandler = ModuleType("globalPluginHandler")
		globalPluginHandler.GlobalPlugin = FakeGlobalPlugin
		cls._stubNames = {
			"appModuleHandler": appModuleHandler,
			"globalPluginHandler": globalPluginHandler,
		}
		cls._originalModules = {name: sys.modules.get(name) for name in cls._stubNames}
		sys.modules.update(cls._stubNames)
		cls.moduleName = "globalPlugins.terminalCopy"
		cls.module = importlib.import_module(cls.moduleName)

	@classmethod
	def tearDownClass(cls) -> None:
		sys.modules.pop(cls.moduleName, None)
		for name, original in cls._originalModules.items():
			if original is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = original
		sys.path.remove(cls._addonPath)

	def setUp(self) -> None:
		self.calls.clear()
		FakeGlobalPlugin.lifecycle.clear()

	def testRegistersUniqueAppModuleAndUnregistersOnce(self) -> None:
		"""The plugin maps only Windows Terminal and releases its mapping once."""
		plugin = self.module.GlobalPlugin()
		self.assertEqual(FakeGlobalPlugin.lifecycle, ["base initialized"])
		self.assertEqual(
			self.calls,
			[("register", "windowsterminal", "terminalCopyWindowsterminal")],
		)
		plugin.terminate()
		plugin.terminate()
		self.assertEqual(self.calls[-1], ("unregister", "windowsterminal"))
		self.assertEqual(self.calls.count(("unregister", "windowsterminal")), 1)
		self.assertEqual(
			FakeGlobalPlugin.lifecycle,
			["base initialized", "base terminated", "base terminated"],
		)

	def testReloadRegistersMappingAgain(self) -> None:
		"""Reloading the global plugin restores the mapping after cleanup."""
		firstPlugin = self.module.GlobalPlugin()
		firstPlugin.terminate()
		secondPlugin = self.module.GlobalPlugin()
		self.assertEqual(
			self.calls,
			[
				("register", "windowsterminal", "terminalCopyWindowsterminal"),
				("unregister", "windowsterminal"),
				("register", "windowsterminal", "terminalCopyWindowsterminal"),
			],
		)
		secondPlugin.terminate()


if __name__ == "__main__":
	unittest.main()
