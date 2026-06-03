# Commit Message Convention

This repository uses [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. The `scripts/normalize-commit-msg.sh` hook enforces this format automatically when installed.

## Format

```
<type>[(<scope>)][!]: <subject>

[optional body]

[optional footers]
```

- **type** — required, lowercase (see valid types below)
- **scope** — optional, parenthesized, e.g. `feat(auth): ...`
- **!** — optional breaking-change marker, e.g. `feat!: ...` or `feat(api)!: ...`
- **subject** — required, brief description, max 72 characters
- **body** — optional, separated from subject by a blank line
- **footers** — optional key/value pairs (e.g. `Fixes: #123`)

## Valid Types

| Type       | When to use                                              |
|------------|----------------------------------------------------------|
| `feat`     | New feature or capability                                |
| `fix`      | Bug fix                                                  |
| `chore`    | Maintenance task that does not affect runtime behavior   |
| `docs`     | Documentation only                                       |
| `refactor` | Code change that is neither a feature nor a bug fix      |
| `test`     | Adding or updating tests                                 |
| `style`    | Formatting, whitespace, or style changes (no logic)      |
| `perf`     | Performance improvement                                  |
| `ci`       | CI/CD pipeline configuration                             |
| `build`    | Build system or dependency changes                       |

## Normalization Rules

The hook applies these transformations automatically:

1. **Lowercase type** — `FEAT:` becomes `feat:`
2. **Separator spacing** — `feat:desc` and `feat:  desc` both become `feat: desc`
3. **Truncate subject** — subject lines longer than 72 characters are hard-truncated with a warning
4. **Strip trailing punctuation** — trailing `.`, `!`, or `?` on the subject line are removed
5. **Skip special commits** — Merge commits and `fixup!`/`squash!` commits are left unchanged

## Examples

**Valid — no changes applied:**
```
feat: add user authentication
fix(db): handle connection timeout
chore: bump go version to 1.22
docs(api): update endpoint reference
feat(auth)!: remove legacy token support
```

**Invalid — hook normalizes automatically:**
```
# Before                          -> After
FEAT: add user authentication     -> feat: add user authentication
fix:handle connection timeout     -> fix: handle connection timeout
Chore: bump go version.           -> chore: bump go version
FIX(DB): resolve null crash!      -> fix(DB): resolve null crash
```

**Cannot be normalized — hook warns and passes through:**
```
# Messages with no type prefix are warned but not rejected:
update the readme
WIP changes
```

## Installation

Install the hook for the current repository:

```bash
bash scripts/install-commit-hook.sh
```

Install globally for all repositories:

```bash
bash scripts/install-commit-hook.sh --global
```

Install for a specific repository path:

```bash
bash scripts/install-commit-hook.sh --repo-path /path/to/repo
```

## Testing

Run the test suite:

```bash
bash tests/test_normalize_commit_msg.sh
```

Test manually with a temporary file:

```bash
echo "FEAT: add something." > /tmp/test-msg.txt
bash scripts/normalize-commit-msg.sh /tmp/test-msg.txt
cat /tmp/test-msg.txt
# Output: feat: add something
```

Or via stdin:

```bash
echo "FIX: resolve crash." | bash scripts/normalize-commit-msg.sh
# Output: fix: resolve crash
```
