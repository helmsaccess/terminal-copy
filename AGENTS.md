# Repository instructions for coding agents

This file defines repository-wide rules for an NVDA add-on based on the official
NVDA AddonTemplate. More specific `AGENTS.md` files may add rules for their subtree.
System, developer, and explicit user instructions take precedence.

## Mission and non-negotiable principles

- Build an accessible, reliable, and maintainable NVDA add-on.
- Prefer documented NVDA and platform APIs. Isolate compatibility workarounds and
  explain why they are necessary.
- Keep user interaction, domain logic, external I/O, persistence, and presentation
  separated so each can be tested independently.
- Never block NVDA's main thread with network I/O, subprocess waits, expensive
  parsing, retries, or diagnostic logging.
- Fail open where practical: internal errors or unavailable integrations must not
  prevent normal NVDA or application behavior.
- Treat external input, discovered resources, IPC messages, and configuration data
  as untrusted until authenticated where applicable and validated.
- Preserve user privacy. Do not log document content, credentials, tokens, or other
  sensitive data unless the user explicitly requests a narrowly scoped diagnostic.

## Repository map

- `addon/`: installable add-on payload, including global plugins, app modules,
  synth drivers, Braille display drivers, resources, and localization data selected
  by the project.
- `buildVars.py`: add-on metadata, versioning, included files, and build settings.
- `manifest.ini.tpl` and localized manifest files: source metadata consumed by the
  build; keep fields aligned with current NVDA add-on requirements.
- `sconstruct` and `site_scons/`: official build and packaging infrastructure.
- `docs/`: user and developer documentation. Follow `docs/AGENTS.md`.
- `tests/`: automated checks for project behavior and template integrity.
- `.github/`: contribution forms and continuous-integration workflows.

## Working rules

- Inspect relevant code, tests, build configuration, and authoritative documentation
  before editing.
- Make reversible, in-scope assumptions explicit. Ask before consequential or
  irreversible architectural choices.
- Preserve established component boundaries and reuse existing structures before
  adding new layers or parallel paths.
- Prefer simplification and deletion when tests show that required behavior remains.
- Preserve unrelated user changes and keep each change focused.
- Before web research, inspect `../nvda-shared-aux/` for reusable NVDA core,
  AddonTemplate, other add-on source, and durable cross-add-on references. Store newly
  acquired material there when it is likely to remain useful for other NVDA add-ons.
- Derive a short, stable abbreviation specifically from the add-on's name and use
  `../<add-on-abbreviation>-aux/` for add-on-specific temporary sources, downloaded
  tools, test workspaces, reproductions, and reports. Do not derive the abbreviation
  from the repository owner, organization, branch, or current task. Neither auxiliary
  directory replaces documented runtime paths or tool-owned ignored output directories.
- For this add-on, the fixed add-on-specific auxiliary directory is `../tc-aux/`.
- Never commit private paths, hostnames, usernames, credentials, tokens, or secrets.
- Follow the conventions of the component and upstream APIs being changed.
- Avoid meta-commentary about instructions, process, or text organization. State the
  actionable rule or result directly unless context is necessary for safety or traceability.
- Logging is diagnostic only; correctness must never depend on it.
- Do not add unowned TODOs. Record deliberate follow-up work with a clear scope and a
  durable issue or design reference.
- Add a regression test for a bug fix whenever practical.
- Update affected documentation in the same change when behavior, compatibility,
  configuration, architecture, development workflow, or release state changes.

## Python and NVDA code style

- Follow PEP 8 except where NVDA's documented conventions or the repository's Ruff
  configuration intentionally differ.
- Indent Python with one tab per level, use UTF-8 and LF line endings, and keep lines
  within 110 characters unless readability clearly requires otherwise.
- Use descriptive lower camel case for functions, methods, variables, and properties;
  upper camel case for classes; and upper snake case for constants.
- Prefix gesture handlers with `script_` and NVDA event handlers with `event_`, keeping
  the subsequent words in NVDA's established camel-case form.
- Give boolean values and predicates positive question-like names such as `isReady`,
  `hasFocus`, or `shouldAnnounce`; avoid double negatives.
- Add PEP 484 type annotations to new code. Use `X | Y` and `T | None` rather than the
  legacy `typing.Union` and `typing.Optional` forms where the supported Python version
  permits them.
- Use PEP 257 docstrings with Sphinx field syntax where parameter or return documentation
  is needed. Put type information in annotations rather than duplicating it in docstrings.
- Every translatable user-facing string must use the appropriate gettext function and
  have a preceding `# Translators:` comment that explains its context.
- Avoid mutable module-level state and work performed during import. Prefer explicit
  initialization, termination, and accessor functions.
- Use `# noqa: <code>  # explanation` only for a deliberate exception that cannot be
  expressed more clearly in code or configuration.

## Accessibility and NVDA integration

- Keep Windows Terminal-specific scripts, events, UIA access, and lifecycle in
  `addon/appModules/windowsterminal.py` or its private package. Add a global plugin
  only for behavior that genuinely requires process-wide lifetime or executable
  mapping, and document and test that exception.
- Define contextual commands with NVDA's `@script` decorator, including translated
  descriptions and categories, so bindings remain discoverable and remappable.
- Use speech, Braille, tones, and focus changes intentionally; avoid duplicate or
  surprising output.
- Respect NVDA configuration profiles, sleep mode, input help, secure mode, and the
  user's speech and Braille settings where relevant.
- Keep gesture names, localized labels, and help text synchronized with the actual
  implementation.
- Avoid relying on timing when an event, state transition, or explicit completion
  signal is available.
- Marshal callbacks to NVDA's main thread only for work that requires it, and keep
  that work short.
- Clean up hooks, threads, subprocesses, sockets, timers, and temporary resources on
  termination and partial initialization failure.

## Validation

- Run the smallest relevant checks while developing, then the complete supported
  suite before handing a change back.
- With the official Python environment installed, use `uv sync` to create the locked
  development environment.
- Run `uv run prek run --all-files` for repository-wide static checks.
- Run the project's unit tests according to its documented test entry point.
- Run `uv run scons` to build the add-on and `uv run scons pot` when localization
  templates are affected.
- Treat failures caused by a restricted environment as environment limitations, not
  successful validation. Re-run affected checks in a suitable environment before
  publication.
- Inspect the final `.nvda-addon` archive and verify that its manifests, documentation,
  localization files, and payload match the intended source state.
- Rebuild affected distributable artifacts from the final worktree before handoff.

## Build and generated files

- Use the official SCons entry points and extend them only for a demonstrated project
  need.
- Keep the base and translated manifest templates aligned with the current official
  AddonTemplate field sets. Strict tests must validate the templates, rendered scalar
  values, compatibility range, update channel, and installed HTML help contract.
- Configure the add-on through `buildVars.py` and source templates instead of editing
  generated manifests, catalogs, HTML, or package archives.
- Keep reproducible generated output out of version control unless the repository
  explicitly documents it as a committed artifact.
- Pin or lock build dependencies and review dependency changes as carefully as source
  changes.

## Git, versioning, and releases

- Never use destructive Git operations or discard work that may belong to the user.
- Do not push, merge, tag, publish a package, or create a GitHub release without
  explicit user authorization.
- Use focused branches and coherent English commit messages for substantial changes.
- The user owns version numbers, release channels, tags, and publication approval.
- Treat a tag as a publication action: the official workflow may build and publish a
  GitHub release for every pushed tag.
- Before publication, validate the base and localized manifests against the current
  official NVDA AddonTemplate and NVDA add-on requirements. Unknown, malformed, or
  empty applicable fields are release blockers.
- Verify the tag target, release metadata, artifact names, checksums where used, and
  successful downloads after publication.

## Documentation

- Keep documentation accurate, task-oriented, internally consistent, and appropriate
  for its audience.
- Preserve the project's configured source language and update maintained translations
  or mirrors in the same change so they make equivalent claims.
- Describe current behavior in current-facing documentation; keep historical behavior
  in changelogs, dated reports, and superseded design records.
- State support, testing, security, and compatibility as risk-based evidence. Do not
  imply exhaustive coverage or response-time guarantees.
- Use exact localized UI labels and gesture names from source catalogs.
- Build generated documentation through repository tools and validate links and output;
  do not edit generated HTML by hand.
