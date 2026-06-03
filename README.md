# Commit Message Normalizer

A git `commit-msg` hook that normalizes commit messages to [Conventional Commits](https://www.conventionalcommits.org/) format. Pure bash, no external dependencies.

## What it does

- Lowercases the type token (`FEAT:` -> `feat:`)
- Normalizes the colon-space separator (`feat:desc` -> `feat: desc`)
- Truncates subject lines longer than 72 characters
- Strips trailing punctuation (`.`, `!`, `?`) from the subject
- Preserves scope, breaking-change markers (`!`), and the commit body
- Skips Merge commits and `fixup!`/`squash!` commits unchanged

## Files

```
scripts/normalize-commit-msg.sh   # the hook/normalizer script
scripts/install-commit-hook.sh    # installs the hook into a git repo
tests/test_normalize_commit_msg.sh # test suite
docs/commit-convention.md         # full convention reference
```

## Quick start

```bash
# Install for the current repo
bash scripts/install-commit-hook.sh

# Install globally
bash scripts/install-commit-hook.sh --global

# Run tests
bash tests/test_normalize_commit_msg.sh
```

See [docs/commit-convention.md](docs/commit-convention.md) for the full convention reference, valid types, and examples.
