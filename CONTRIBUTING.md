# Contributing to Terminal Copy

Create a focused working branch from `main`. Keep unrelated changes out of
the diff and use English for commits and pull requests. Update tests, the
English and German guides when behavior changes, and `Unreleased` in
[the changelog](changelog.md) for notable changes.

Self-review the diff and run the relevant
[checks](docs/release-and-versioning.md#build-and-verify). Push the working
branch and open a GitHub pull request targeting `main`. Include why the
change is needed, a changelog covering the full diff, test results and
known limits. Link related issues and use a draft if the work is incomplete.

Every change to `main` goes through a pull request, including hotfixes and
release preparation. Direct pushes to `main` are prohibited. Merge with
maintainer approval after required checks pass and blocking review comments
are resolved. Request independent review when an eligible reviewer is
available and follow the repository's configured approval rules.

Coding agents push validated working branches independently. The owner
explicitly approves each pull request they open, including drafts. Merge,
tagging and publication require separate approval.

Maintainers can enforce the PR requirement, successful build check, resolved
conversations, and limits on deletion and force pushes through a GitHub
ruleset on `main`, including for administrators.
[GitHub pull request guidance](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes) ·
[GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
