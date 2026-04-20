# Commit Message Normalizer

A command-line tool that standardizes commit messages to the [Conventional Commits](https://www.conventionalcommits.org/) format.

## What it does

- Lowercases the commit type (`FIX:` -> `fix:`)
- Replaces unknown types with `chore`
- Normalizes scope whitespace and removes empty scopes
- Strips trailing periods from the description
- Lowercases the first character of the description
- Truncates the subject line to 72 characters
- Preserves body and footer paragraphs

## Installation

```sh
pip install -e .
```

## CLI Usage

### Normalize a string argument

```sh
commit-normalize "Feat: Add new thing."
# feat: add new thing
```

### Normalize a file in place (git hook usage)

```sh
commit-normalize --file .git/COMMIT_EDITMSG
# or with the short flag
commit-normalize -f .git/COMMIT_EDITMSG
```

### Read from stdin and write to stdout

Pass `-` as the file argument to read from stdin:

```sh
echo "FIX: Correct the typo." | commit-normalize --file -
# fix: correct the typo

git log -1 --format=%B | commit-normalize --file -
```

## Git Hook Setup

To automatically normalize every commit message, install as a `commit-msg` hook:

```sh
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/sh
commit-normalize --file "$1"
EOF
chmod +x .git/hooks/commit-msg
```

The hook receives the path to the commit message file as its first argument and rewrites it in place before the commit is recorded.

### Shared hook (via core.hooksPath)

If your project uses a shared hooks directory:

```sh
mkdir -p .githooks
cat > .githooks/commit-msg << 'EOF'
#!/bin/sh
commit-normalize --file "$1"
EOF
chmod +x .githooks/commit-msg
git config core.hooksPath .githooks
```

## Running Tests

```sh
pytest
```
