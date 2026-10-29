# Contributing to Wisp MCP

Bug reports, reproducible compatibility problems, documentation improvements and focused patches are welcome.

## Before opening an issue

Check the existing issues and the current documentation. Describe the WISP panel behavior, MCP version, reproduction steps and expected result. Use sanitized examples. Never include real tokens, server credentials, customer files or private logs.

For security vulnerabilities, follow [SECURITY.md](SECURITY.md) rather than opening a public issue.

## Proposing a change

1. Open an issue first for substantial API, permissions, transport or behavior changes.
2. Keep each pull request focused on one problem.
3. Include or update tests for behavioral changes, especially security gates and destructive operations.
4. Preserve compatibility with the documented WISP Client API; do not add provider-specific assumptions without evidence.
5. Explain the user-visible change and link the related issue when there is one.

## Local checks

Requires Python 3.11 or newer.

~~~bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src/wisp_mcp
bandit -q -r src
pytest
python -m build
~~~

The CI also validates packaging and integration metadata. A local check does not replace review of changes to authentication, remote deployment or privileges.

## License and attribution

The public code is distributed under **PolyForm Noncommercial 1.0.0**, not an OSI-approved open-source license. Contributions are accepted for distribution under the repository's existing terms unless separately agreed in writing. Do not add dependencies or contributions whose licensing conflicts with those terms.

Keep authorship and third-party notices accurate. Do not submit credentials, panel exports, generated environments or unrelated formatting changes.
