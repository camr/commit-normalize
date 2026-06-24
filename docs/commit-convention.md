# Commit Message Convention

This repository enforces [Conventional Commits](https://www.conventionalcommits.org/) format via a git commit-msg hook.

## Format

```
<type>[(<scope>)][!]: <description>

[optional body]

[optional footer(s)]
```

- `type`: lowercase keyword describing the change category (required)
- `scope`: short noun describing the code area affected (optional, in parentheses)
- `!`: marks a breaking change (optional)
- `description`: short summary in present tense, max 72 characters total on the subject line

## Accepted Types

| Type       | When to use                                          |
|------------|------------------------------------------------------|
| `feat`     | A new feature                                        |
| `fix`      | A bug fix                                            |
| `chore`    | Build process, tooling, or maintenance changes       |
| `docs`     | Documentation-only changes                          |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test`     | Adding or updating tests                             |
| `ci`       | Changes to CI/CD configuration and scripts           |
| `style`    | Formatting, whitespace, missing semicolons, etc.     |
| `perf`     | Performance improvements                             |
| `build`    | Changes affecting build system or external dependencies |
| `revert`   | Reverts a previous commit                            |

## Examples

```
feat: add user authentication
feat(auth): add oauth2 login support
fix(parser): handle empty input gracefully
fix!: drop support for Node 14
chore: update dependencies
docs(readme): add installation instructions
refactor(db): extract connection pool helper
test(api): add integration tests for /users endpoint
ci: add GitHub Actions workflow
```

## Normalization

The commit-msg hook (`tools/commit-normalize.sh`) automatically:

- Lowercases the type token (`FEAT` -> `feat`)
- Normalizes the colon separator to `": "` (exactly one space after colon)
- Truncates the subject line to 72 characters
- Strips a trailing period from the subject line
- Skips Merge commits and fixup/squash commits without modification

If the message cannot be normalized (unrecognized type, missing colon separator), the commit is rejected with an error explaining the expected format.

## Installation

```bash
# Install hook for the current repository
bash tools/install-hooks.sh

# Install globally for all repositories
bash tools/install-hooks.sh --global
```
