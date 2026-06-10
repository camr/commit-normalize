# Commit Message Normalizer

A standalone Python script (`normalize.py`) that enforces a consistent
conventional-commits format on git commit messages. Drop it in as a
`commit-msg` hook and every commit gets normalized automatically.

## Rules

- Git comment lines (lines starting with `#`) are stripped before processing.
- Subject first word is capitalized.
- Trailing period on subject is removed.
- Subject line is trimmed to 72 characters at the nearest word boundary.
- A blank line is enforced between subject and body.
- Body lines are wrapped at 72 characters.
- Git trailers (`Token: value` lines such as `Co-authored-by:`, `Fixes:`,
  `BREAKING CHANGE:`) are preserved verbatim and never reflowed into body prose.

Non-conventional subjects (those that do not start with `type:` or
`type(scope):`) still receive capitalization, period removal, and
length trimming.

## Usage

### As a git hook

```sh
cp normalize.py .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

Git will invoke `normalize.py <path-to-COMMIT_EDITMSG>` automatically
before the commit is recorded. The file is normalized in-place.

### From stdin

```sh
echo "feat: add widget." | python normalize.py
# -> feat: Add widget
```

### Check mode (CI)

Pass `--check` to verify a message is already normalized without modifying it.
Exits `0` if no changes are needed; exits `1` and prints a diff-style report
if the message would change.

```sh
# As a pre-push or CI lint step:
python normalize.py --check .git/COMMIT_EDITMSG

# Pipe from stdin:
echo "feat: add widget." | python normalize.py --check
```

`--check` can be combined with a file path or used with stdin. The file is
never written in check mode.

### Programmatic

```python
from normalize import normalize

msg = normalize("feat: add widget.\n\nsome body text")
```

## Example

Input:

```
feat: add new login flow.

this change adds oauth2 support for the login endpoint, which was
previously unsupported and required a workaround.
```

Output:

```
feat: Add new login flow

This change adds oauth2 support for the login endpoint, which was
previously unsupported and required a workaround.
```

## Development

```sh
pip install -e ".[dev]"
pytest
```
