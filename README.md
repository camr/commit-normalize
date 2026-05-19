# Commit Message Normalizer

A portable shell-script git `commit-msg` hook that validates and auto-corrects
commit messages to follow the [Conventional Commits](https://www.conventionalcommits.org/)
specification.

## Supported Commit Types

| Type       | Purpose                                    |
|------------|--------------------------------------------|
| `feat`     | A new feature                              |
| `fix`      | A bug fix                                  |
| `docs`     | Documentation changes only                 |
| `chore`    | Build process or auxiliary tool changes    |
| `refactor` | Code change that neither fixes nor adds     |
| `test`     | Adding or correcting tests                 |
| `style`    | Formatting, whitespace, missing semicolons |
| `perf`     | Performance improvement                    |
| `ci`       | CI/CD configuration changes                |

## Format

```
<type>[(<scope>)][!]: <subject>

[optional body]
```

Examples:

```
feat: Add user authentication
fix(api): Correct null pointer in response handler
docs: Update installation instructions
chore!: Drop support for Node 16
```

## Normalization Rules

1. **Type prefix required** - messages without a type get one inferred from the description.
2. **Type lowercased** - `FEAT:` becomes `feat:`.
3. **Subject capitalized** - first word of the description is capitalized.
4. **No trailing period** - a trailing `.` is removed; `...` (ellipsis) is preserved.
5. **72-char subject limit** - subject lines longer than 72 characters are truncated with a warning.
6. **Blank line separator** - a blank line is inserted between subject and body when both are present.
7. **Git comment lines stripped** - lines beginning with `#` are ignored.

## Installation

Run the installer from inside your git repository:

```sh
# Symlink (hook updates automatically when the script changes)
sh /path/to/commit-normalize/scripts/install-hook.sh

# Copy (self-contained, useful for shared repositories)
sh /path/to/commit-normalize/scripts/install-hook.sh --copy

# Verify the hook is installed
sh /path/to/commit-normalize/scripts/install-hook.sh --check
```

The installer backs up any pre-existing `commit-msg` hook before installing.

## Manual Usage

The hook can also be run directly:

```sh
sh scripts/commit-msg path/to/COMMIT_EDITMSG
```

## Running Tests

```sh
sh tests/test_commit_msg.sh
```

## Files

```
scripts/
  commit-msg        - the git hook (copy or symlink into .git/hooks/)
  install-hook.sh   - installer script
tests/
  test_commit_msg.sh - test suite (24 tests)
```
