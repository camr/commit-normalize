# Commit Message Normalizer

Normalize commit messages to [Conventional Commits](https://www.conventionalcommits.org/) format.

## Installation

```bash
pip install -e .
```

This installs the `commit-normalize` command.

## Usage

**Normalize a string directly:**

```bash
commit-normalize "add login endpoint"
# output: chore: add login endpoint

commit-normalize "feat: Add user authentication."
# output: feat: add user authentication

commit-normalize "fix(auth)!: prevent session fixation"
# output: fix(auth)!: prevent session fixation
```

**Normalize a file in place (for use in hooks):**

```bash
commit-normalize -f /path/to/COMMIT_EDITMSG
```

## Git commit-msg Hook Setup

To automatically normalize every commit message, install this as a `commit-msg` hook:

```bash
cat > .git/hooks/commit-msg <<'EOF'
#!/bin/sh
commit-normalize -f "$1"
EOF
chmod +x .git/hooks/commit-msg
```

The hook rewrites the file at `$1` in place before git records it.

## Behavior Notes

- **Unknown types** (anything not in the Conventional Commits type list) are mapped to `chore`.
- **Subject line** is truncated to 72 characters maximum.
- **Breaking change marker** (`!`) is preserved when present in the original header.
- **Trailing period** is stripped from the description.
- **Scope** whitespace is normalized; whitespace-only scopes are discarded.
- **Body and footers** are passed through unchanged.
