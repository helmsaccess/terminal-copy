# Changelog

## Unreleased

### Added

- Copy marked text in classic Windows Command Prompt using the same review-cursor gestures
  as in Windows Terminal. Use the console text exposed by NVDA through UI Automation or its
  legacy console backend.

### Changed

- Confirm compatibility with NVDA 2026.3.1 and update the manifest's last-tested API version.
- Update the English and German manifest summaries to describe classic Command Prompt support.
- Give SCons development archives a branch-local build identifier while keeping the NVDA manifest
  version numeric. Validate the product version and keep release artifacts independent of GitHub publication.
- Build and verify tag artifacts in CI. Publish the single add-on from an approved GitHub release draft.
- Document the pull request, changelog, and NVDA Add-on Store release rules.

## [0.1.1] - 2026-08-26

Terminal Copy now uses a uniquely named AppModule mapping. It continues to work on its own and can
preserve the commands, events, overlays, and lifecycle of another add-on's direct Windows Terminal
AppModule.

## [0.1] - 2026-08-15

Terminal Copy lets NVDA users mark and copy regions from Windows Terminal with the review cursor,
including available scrollback outside the visible viewport. Use `NVDA+R` to set the two marks and
`NVDA+C` to copy the region. The add-on includes English and German interfaces and help.

The two-mark interaction is adapted from
[Terminal Access for NVDA](https://github.com/PratikP1/Terminal-Access-for-NVDA) by Pratik Patel.
Terminal Access in turn credits [TDSR](https://github.com/tspivey/tdsr) by Tyler Spivey and
[Speakup](https://github.com/linux-speakup/speakup), the Linux kernel screen reader, as inspirations.

[0.1.1]: https://github.com/helmsaccess/terminal-copy/releases/tag/v0.1.1
[0.1]: https://github.com/helmsaccess/terminal-copy/releases/tag/v0.1
