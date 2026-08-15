"""Strict tests for Terminal Copy's NVDA manifest and installed help contract."""

from __future__ import annotations

from pathlib import Path, PurePath
import re
import shutil
import tempfile
import unittest
from urllib.parse import urlsplit

import buildVars
from site_scons.site_tools.NVDATool.docs import md2html


ROOT = Path(__file__).parents[2]
BASE_MANIFEST_FIELDS = (
	"name",
	"summary",
	"description",
	"author",
	"url",
	"version",
	"changelog",
	"docFileName",
	"minimumNVDAVersion",
	"lastTestedNVDAVersion",
	"updateChannel",
)
LOCALIZED_MANIFEST_FIELDS = ("summary", "description", "changelog")
MULTILINE_MANIFEST_FIELDS = frozenset(("description", "changelog"))
OFFICIAL_BASE_TEMPLATE = '''name = {addon_name}
summary = "{addon_summary}"
description = """{addon_description}"""
author = "{addon_author}"
url = {addon_url}
version = {addon_version}
changelog = """{addon_changelog}"""
docFileName = {addon_docFileName}
minimumNVDAVersion = {addon_minimumNVDAVersion}
lastTestedNVDAVersion = {addon_lastTestedNVDAVersion}
updateChannel = {addon_updateChannel}
'''
OFFICIAL_LOCALIZED_TEMPLATE = '''summary = "{addon_summary}"
description = """{addon_description}"""
changelog = """{addon_changelog}"""
'''
API_VERSION = re.compile(r"^(?:0|[1-9]\d{3})\.\d+(?:\.\d+)?$")
ADDON_VERSION = re.compile(r"^\d+\.\d+(?:\.\d+)?$")
ADDON_NAME = re.compile(r"^[a-z][A-Za-z0-9]*$")
AUTHOR_WITH_EMAIL = re.compile(r"^.+\s<[^<>\s@]+@[^<>\s@]+>$")


def parseManifest(text: str) -> dict[str, str]:
	"""Parse the scalar subset emitted by the official manifest template."""
	result: dict[str, str] = {}
	lines = iter(text.splitlines())
	for line in lines:
		match = re.fullmatch(r"([A-Za-z][A-Za-z0-9]*) = (.*)", line)
		if match is None:
			raise AssertionError(f"Malformed manifest line: {line!r}")
		key, rawValue = match.groups()
		if key in result:
			raise AssertionError(f"Duplicate manifest field: {key}")
		if rawValue.startswith('"""'):
			valueParts = [rawValue[3:]]
			while not valueParts[-1].endswith('"""'):
				try:
					valueParts.append(next(lines))
				except StopIteration as error:
					raise AssertionError(f"Unterminated manifest field: {key}") from error
			valueParts[-1] = valueParts[-1][:-3]
			value = "\n".join(valueParts)
		elif rawValue.startswith('"') and rawValue.endswith('"'):
			value = rawValue[1:-1]
		else:
			value = rawValue
		result[key] = value
	return result


def versionTuple(value: str) -> tuple[int, int, int]:
	"""Normalize a two- or three-part version for ordering."""
	parts = [int(part) for part in value.split(".")]
	return tuple((parts + [0])[:3])


class TestManifestContract(unittest.TestCase):
	"""Validate official templates, project metadata, and generated help."""

	def testTemplatesMatchCurrentOfficialAddonTemplate(self) -> None:
		"""The checked-in templates retain the exact official scalar field contracts."""
		self.assertEqual(
			OFFICIAL_BASE_TEMPLATE,
			(ROOT / "manifest.ini.tpl").read_text(encoding="utf-8"),
		)
		self.assertEqual(
			OFFICIAL_LOCALIZED_TEMPLATE,
			(ROOT / "manifest-translated.ini.tpl").read_text(encoding="utf-8"),
		)

	def testRenderedManifestIsCompleteAndValid(self) -> None:
		"""Every official field renders as one valid, non-empty scalar value."""
		manifest = parseManifest(OFFICIAL_BASE_TEMPLATE.format(**buildVars.addon_info))
		self.assertEqual(BASE_MANIFEST_FIELDS, tuple(manifest))
		for field, value in manifest.items():
			with self.subTest(field=field):
				self.assertTrue(value)
				self.assertEqual(value, value.strip())
				self.assertNotIn("\x00", value)
				self.assertNotIn("\r", value)
				if field not in MULTILINE_MANIFEST_FIELDS:
					self.assertNotIn("\n", value)
		self.assertRegex(manifest["name"], ADDON_NAME)
		self.assertRegex(manifest["author"], AUTHOR_WITH_EMAIL)
		self.assertRegex(manifest["version"], ADDON_VERSION)
		self.assertRegex(manifest["minimumNVDAVersion"], API_VERSION)
		self.assertRegex(manifest["lastTestedNVDAVersion"], API_VERSION)
		self.assertLessEqual(
			versionTuple(manifest["minimumNVDAVersion"]),
			versionTuple(manifest["lastTestedNVDAVersion"]),
		)
		url = urlsplit(manifest["url"])
		self.assertEqual("https", url.scheme)
		self.assertTrue(url.hostname)
		self.assertIsNone(url.username)
		self.assertIsNone(url.password)
		self.assertEqual("None", manifest["updateChannel"])
		self.assertIsNone(buildVars.addon_info["addon_updateChannel"])

	def testProjectIdentityAndBuildOnlyMetadataStayAligned(self) -> None:
		"""User identity, compatibility, and Store-only fields remain intentional."""
		manifest = parseManifest(OFFICIAL_BASE_TEMPLATE.format(**buildVars.addon_info))
		self.assertEqual("terminalCopy", manifest["name"])
		self.assertEqual("Terminal Copy", manifest["summary"])
		self.assertEqual("0.1", manifest["version"])
		self.assertEqual("Emanuel Helms <emanuel@helmsaccess.de>", manifest["author"])
		self.assertEqual("https://github.com/helmsaccess/terminal-copy", manifest["url"])
		self.assertEqual("2026.1.0", manifest["minimumNVDAVersion"])
		self.assertEqual("2026.1.1", manifest["lastTestedNVDAVersion"])
		self.assertNotIn("development", manifest["changelog"].casefold())
		self.assertNotIn("sourceURL", manifest)
		self.assertNotIn("license", manifest)
		self.assertEqual(manifest["url"], buildVars.addon_info["addon_sourceURL"])
		self.assertEqual(
			"GNU General Public License version 2 or later",
			buildVars.addon_info["addon_license"],
		)

	def testInstalledHelpNameAndGeneratedHtmlStayAligned(self) -> None:
		"""The manifest help target is portable HTML generated from the concise guide."""
		docFileName = buildVars.addon_info["addon_docFileName"]
		self.assertEqual(PurePath(docFileName).name, docFileName)
		self.assertEqual(".html", PurePath(docFileName).suffix.casefold())
		readme = ROOT / "readme.md"
		self.assertTrue(readme.is_file())
		with tempfile.TemporaryDirectory() as temporary:
			languageDirectory = Path(temporary) / buildVars.baseLanguage
			languageDirectory.mkdir()
			markdownPath = languageDirectory / "readme.md"
			shutil.copyfile(readme, markdownPath)
			htmlPath = languageDirectory / docFileName
			md2html(
				markdownPath,
				htmlPath,
				moFile=None,
				mdExtensions=buildVars.markdownExtensions,
				addon_info=buildVars.addon_info,
			)
			html = htmlPath.read_text(encoding="utf-8")
		self.assertIn('<html lang="en">', html)
		self.assertIn("<title>Terminal Copy 0.1</title>", html)
		self.assertIn("<h1>Terminal Copy</h1>", html)
		self.assertIn("NVDA+R", html)
		self.assertIn("NVDA+C", html)
		self.assertNotIn("development version", html.casefold())

	def testGermanHelpGeneratesInstallableHtml(self) -> None:
		"""The German guide has equivalent tasks and generates localized HTML."""
		markdownPath = ROOT / "addon" / "doc" / "de" / "readme.md"
		self.assertTrue(markdownPath.is_file())
		with tempfile.TemporaryDirectory() as temporary:
			htmlPath = Path(temporary) / "readme.html"
			md2html(
				markdownPath,
				htmlPath,
				moFile=None,
				mdExtensions=buildVars.markdownExtensions,
				addon_info=buildVars.addon_info,
			)
			html = htmlPath.read_text(encoding="utf-8")
		self.assertIn('<html lang="de">', html)
		self.assertIn("<h1>Terminal Copy</h1>", html)
		self.assertIn("NVDA+R", html)
		self.assertIn("NVDA+C", html)
		self.assertIn("Leerraum", html)
		self.assertIn("Pratik Patel", html)
		self.assertNotIn("entwicklungsversion", html.casefold())

	def testGermanCatalogSourceExists(self) -> None:
		"""The German gettext source is present and identifies its locale."""
		catalog = ROOT / "addon" / "locale" / "de" / "LC_MESSAGES" / "nvda.po"
		text = catalog.read_text(encoding="utf-8")
		self.assertIn('"Language: de\\n"', text)
		self.assertIn('msgstr "Bereichsmarken gelöscht"', text)
		self.assertNotIn("#, fuzzy", text)

	def testLocalizedTemplateContainsOnlyLocalizableOfficialFields(self) -> None:
		"""Localized manifests cannot override identity or compatibility metadata."""
		localized = parseManifest(OFFICIAL_LOCALIZED_TEMPLATE.format(**buildVars.addon_info))
		self.assertEqual(LOCALIZED_MANIFEST_FIELDS, tuple(localized))
		self.assertTrue(all(value and value == value.strip() for value in localized.values()))

	def testPackageExcludesDevelopmentOnlyPayload(self) -> None:
		"""Documentation sources, translation sources, and bytecode stay outside the package."""
		self.assertEqual(["*.md", "*.po", "*.pyc"], buildVars.excludedFiles)


if __name__ == "__main__":
	unittest.main()
