# Versioning and releases

## Versions and channels

`buildVars.py` owns the product version, release channel and NVDA
compatibility fields. The manifest always contains the numeric version
`X.Y.Z` without leading zeroes. Development archives use
`terminalCopy-X.Y.Z-dev.N+branch.commit.nvda-addon` when Git metadata is
available. Start `development_build` at 1 on each branch's first changed
installable state and increment it for later installable changes. Rebuilding
the same state may reuse the number. Use `development_build = None` for
an approved release state, which produces `terminalCopy-X.Y.Z.nvda-addon`.
Use isolated NVDA profiles for development builds and distinct numeric
versions to test updates.

Use PATCH for compatible fixes, MINOR for compatible features and
deprecations, and MAJOR from 1.0.0 for breaks in promised compatibility.
For Terminal Copy this includes the supported NVDA versions, supported
terminal behavior and documented gestures. Before 1.0.0, signal deliberate
compatibility breaks with a MINOR bump and explain them in the release notes.
Define the compatibility and upgrade promises before approving 1.0.0.
[SemVer](https://semver.org/spec/v2.0.0.html)

The owner approves the product number and the `stable`, `beta` or `dev`
channel. The template represents stable as `None` in the manifest. Keep
published versions unique across channels and check both GitHub tags and
NVDA Store listings for collisions and update order. Experimental NVDA APIs
require beta or dev in the Store. Historical names, including `v0.1`,
remain valid for their existing releases.
[NVDA Store metadata](https://github.com/nvaccess/addon-datastore/blob/master/docs/design/jsonMetadata.md) ·
[NVDA Store submission guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md)

## Changelog and upgrade notes

Record notable changes as they land under `Unreleased` in the English
`changelog.md`. Use relevant groups such as Added, Changed, Deprecated,
Removed, Fixed and Security. For a release, curate the changes since the
previous GitHub release under `## [X.Y.Z] - YYYY-MM-DD`, link the version to
its tag, and reset `Unreleased`. Update the English and German help in the
same release PR when their version, supported versions or instructions change.

Maintain the concise Store upgrade summary in `addon_changelog` in
`buildVars.py` and update its German gettext translation. Select the
baseline from the actual Store version on the intended upgrade path. For
stable users this is the last stable Store release, even when a newer beta
exists. For the first stable release, cover the oldest published predecessor
on the intended upgrade path. Include relevant changes from intermediate
betas and GitHub-only versions. If the add-on is new to the Store, describe
the initial release. GitHub notes and the Store summary can therefore cover
different spans. [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## Build and verify

Run from the repository root with Python 3.13, uv, and GNU gettext on PATH.

```text
uv sync --locked
uv run prek run --all-files
uv run python -m unittest discover -s tests/unit -v
uv run scons pot
uv run scons
uv run python tests/package/test_built_addon.py
```

The package test checks the exact payload, the generated manifests, and
both installed help files. Update the minimum NVDA API when the supported
minimum changes and the last-tested API after successful compatibility
checks. Verify installation and the applicable Windows Terminal behavior in
isolated NVDA test profiles before release.

## GitHub and NVDA Store

1. Prepare the approved release metadata, changelog, help and translations
   in a [pull request](../CONTRIBUTING.md) against `main`. After the approved
   merge, test the exact clean revision and verify the intended package.
2. After tag approval, place an annotated `vX.Y.Z` tag on that exact commit
   on `main` and push only the tag. CI checks the tag, the version and the
   release build state, then uploads the verified add-on as a workflow artifact.
3. After publication approval, create a GitHub release draft with
   `gh release create --draft --verify-tag --fail-on-no-commits`. Supply
   the existing tag, curated English notes, and exactly one download,
   `terminalCopy-X.Y.Z.nvda-addon`. Confirm the tag target and the SHA-256
   of the uploaded file before publishing. Mark previews as prereleases
   and exclude them from Latest. Reserve Latest for the current stable line.
   Verify the published download and keep the tag and package immutable.
   Package corrections get a new version.
4. Submit to the NVDA Store only after separate approval. Use the direct
   HTTPS URL of the published add-on and its verified SHA-256. Check the
   actual Store listing before using it as the next baseline.

[GitHub CLI](https://cli.github.com/manual/gh_release_create) ·
[Immutable GitHub releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
