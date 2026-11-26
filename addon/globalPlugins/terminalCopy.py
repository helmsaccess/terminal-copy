"""Register Terminal Copy's terminal AppModule mappings."""

from typing import override

import appModuleHandler
import globalPluginHandler


APP_MODULE_MAPPINGS = (
	("windowsterminal", "terminalCopyWindowsterminal"),
	("cmd", "terminalCopyConsole"),
	("conhost", "terminalCopyConsole"),
)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Maintain the executable mapping required by Terminal Copy's app module."""

	def __init__(self) -> None:
		super().__init__()
		self._registered: list[str] = []
		try:
			for executable, module in APP_MODULE_MAPPINGS:
				appModuleHandler.registerExecutableWithAppModule(executable, module)
				self._registered.append(executable)
		except Exception:
			self.terminate()
			raise

	@override
	def terminate(self) -> None:
		"""Remove Terminal Copy's executable mapping when the add-on is unloaded."""
		try:
			while self._registered:
				appModuleHandler.unregisterExecutable(self._registered.pop())
		finally:
			super().terminate()
