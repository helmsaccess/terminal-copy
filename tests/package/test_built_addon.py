"""Validate the exact runtime payload of the built NVDA add-on."""

from __future__ import annotations

import gettext
from io import BytesIO
from pathlib import Path
import sys
import unittest
import zipfile


ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

import buildVars  # noqa: E402  # The repository root is added before importing build metadata.


EXPECTED_FILES = frozenset(
	(
		"manifest.ini",
		"appModules/windowsterminal.py",
		"appModules/terminalCopy/__init__.py",
		"appModules/terminalCopy/selection.py",
		"locale/de/manifest.ini",
		"locale/de/LC_MESSAGES/nvda.mo",
		"doc/style.css",
		"doc/en/readme.html",
		"doc/de/readme.html",
	),
)


class TestBuiltAddon(unittest.TestCase):
	"""Reject missing runtime files and unnecessary development files."""

	@classmethod
	def setUpClass(cls) -> None:
		cls.archivePath = ROOT / (
			f"{buildVars.addon_info['addon_name']}-{buildVars.addon_info['addon_version']}.nvda-addon"
		)
		if not cls.archivePath.is_file():
			raise RuntimeError(f"Build the add-on before running package tests: {cls.archivePath}")

	def testArchiveContainsExactRuntimePayload(self) -> None:
		"""The archive contains every required file and no development-only source."""
		with zipfile.ZipFile(self.archivePath) as archive:
			self.assertIsNone(archive.testzip())
			self.assertEqual(EXPECTED_FILES, set(archive.namelist()))

	def testLocalizedRuntimeContentIsUsable(self) -> None:
		"""German metadata, messages, and both installed help files are present."""
		with zipfile.ZipFile(self.archivePath) as archive:
			baseManifest = archive.read("manifest.ini").decode("utf-8")
			germanManifest = archive.read("locale/de/manifest.ini").decode("utf-8")
			englishHelp = archive.read("doc/en/readme.html").decode("utf-8")
			germanHelp = archive.read("doc/de/readme.html").decode("utf-8")
			translations = gettext.GNUTranslations(
				BytesIO(archive.read("locale/de/LC_MESSAGES/nvda.mo")),
			)
		self.assertIn("name = terminalCopy", baseManifest)
		self.assertIn("version = 0.1", baseManifest)
		self.assertIn("updateChannel = None", baseManifest)
		self.assertNotIn("development", baseManifest.casefold())
		self.assertIn('summary = "Terminal Copy"', germanManifest)
		self.assertIn('<html lang="en">', englishHelp)
		self.assertIn('<html lang="de">', germanHelp)
		self.assertIn("Trailing whitespace is removed from every", englishHelp)
		self.assertIn("Solche Zeilen am Anfang oder Ende werden entfernt", germanHelp)
		self.assertEqual("Bereichsmarken gelöscht", translations.gettext("Region marks cleared"))


if __name__ == "__main__":
	unittest.main()
