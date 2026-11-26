"""Add copy commands while preserving a direct Windows Terminal AppModule."""

from typing import TYPE_CHECKING

import appModuleHandler

from appModules.terminalCopy.regionCopy import RegionCopyAppModule


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


class AppModule(RegionCopyAppModule, BaseAppModule):
	"""Combine Terminal Copy commands with the native or companion module."""
