# Documentation instructions for coding agents

These rules apply to `docs/` and supplement the repository-wide `AGENTS.md`.

## Purpose and audience

- Identify the intended reader and task before writing. Keep quick-start material,
  user guidance, troubleshooting, developer reference, design decisions, and history
  distinct.
- Lead with what the reader can accomplish, then explain prerequisites, steps, expected
  results, limitations, and recovery where needed.
- Use plain, direct language. Introduce NVDA, platform, and add-on terminology before
  relying on it.
- Make documentation usable with screen readers: use meaningful headings and link text,
  simple tables only when they improve comparison, and text alternatives for informative
  images.
- Avoid meta-commentary about the document, its instructions, or the writing process.
  Present useful content directly unless context is necessary for understanding or
  traceability.

## Sources of truth

- Treat the root `readme.md` as the canonical English guide and
  `addon/doc/de/readme.md` as its maintained German counterpart. SCons generates the
  installed `doc/<language>/readme.html`; keep that name aligned with
  `addon_docFileName` and never edit generated copies.
- Verify behavior against current code, tests, manifests, translation catalogs, and
  official NVDA documentation before changing a claim.
- Before web retrieval, inspect `../nvda-shared-aux/` for durable NVDA, AddonTemplate,
  and other add-on references. Preserve newly acquired cross-add-on reference material
  there; use the add-on-specific `../<add-on-abbreviation>-aux/` for project research.
- Treat plans, issues, changelogs, and old design records as historical evidence, not
  proof of current behavior.
- Use exact menu paths, control labels, settings names, and gestures from the maintained
  localization sources.
- Clearly distinguish NVDA commands from operating-system or application shortcuts.

## Structure and maintenance

- Keep each fact in one authoritative place where practical and link to it instead of
  duplicating long instructions.
- Update navigation, indexes, cross-references, examples, and affected translations when
  moving or renaming documentation.
- Keep current implementation, compatibility, and known limitations synchronized with
  behavior changes. Record completed user-visible changes in the changelog.
- Mark obsolete design decisions as superseded and link to the replacement; do not
  silently rewrite historical records.
- Never include credentials, tokens, private hostnames, personal paths, or unredacted
  diagnostic content in examples.

## Localization

- Preserve the configured source language and the repository's translation workflow.
- Maintained language versions must make equivalent technical claims, even when wording
  and sentence structure differ naturally.
- Do not translate code, command names, configuration keys, file names, or identifiers
  unless the product exposes an explicitly localized label.
- Write new user-facing strings so they are concise, contextual, and translatable; avoid
  assembling sentences from fragments.

## Commands and examples

- Make commands safe to copy, state the required shell and working directory when they
  are not obvious, and use placeholders that cannot be mistaken for real secrets.
- Explain destructive, privileged, networked, or publication effects before the command.
- Keep examples minimal but executable. Test them or clearly label pseudocode and
  environment-dependent output.
- Do not promise that a workaround, compatibility boundary, or third-party behavior is
  permanent unless an authoritative source guarantees it.

## Validation and generated output

- Run the repository's documentation checks and link validation after relevant changes.
- Build documentation through the official SCons targets or documented project tools.
- Do not edit generated HTML, catalogs, or packaged documentation by hand; change the
  source and rebuild.
- Inspect generated output for headings, navigation, code blocks, links, localized text,
  and archive contents before publication.
