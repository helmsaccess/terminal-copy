"""Associate Windows Terminal with Terminal Copy's uniquely named app module."""

from typing import override

import appModuleHandler
import globalPluginHandler


EXECUTABLE_NAME = "windowsterminal"
APP_MODULE_NAME = "terminalCopyWindowsterminal"


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Maintain the executable mapping required by Terminal Copy's app module."""

	def __init__(self) -> None:
		super().__init__()
		self._isRegistered = False
		appModuleHandler.registerExecutableWithAppModule(EXECUTABLE_NAME, APP_MODULE_NAME)
		self._isRegistered = True

	@override
	def terminate(self) -> None:
		"""Remove Terminal Copy's executable mapping when the add-on is unloaded."""
		try:
			if self._isRegistered:
				appModuleHandler.unregisterExecutable(EXECUTABLE_NAME)
				self._isRegistered = False
		finally:
			super().terminate()
