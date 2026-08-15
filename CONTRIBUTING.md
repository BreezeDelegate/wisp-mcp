# Contributing

Keep changes focused and compatible with the documented Wisp Client API.

Before opening a pull request:

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python -m build
```

Do not include credentials, panel exports, customer data, generated environment files, or unrelated formatting changes.
