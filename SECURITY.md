# Security

## Running security checks locally

Install all dependencies first:

```bash
pip install -r requirements.txt
```

### 1. Run the test suite (skip test four)

Test four requires a running UDP sound server and audio hardware; it is
intentionally excluded from automated and CI runs.

```bash
# Uses the -k "not test_4" default from pytest.ini
pytest tests/ -v

# To run test four explicitly (needs sound_player.py running separately):
python sound_player.py &
pytest tests/ -k "test_4" -v
```

### 2. Static analysis with Bandit

```bash
bandit -r . --exclude ./.git,./venv,./.venv,./tests --severity-level medium -f txt
```

### 3. Dependency vulnerability audit with pip-audit

```bash
pip-audit -r requirements.txt
```

---

## Known security fixes (this release)

| ID | File | Issue | Fix |
|----|------|-------|-----|
| S1 | `main.py` | `os.system(f"title {TITLE}")` flagged as shell injection risk (B605/High) | Replaced with `ctypes.windll.kernel32.SetConsoleTitleW(TITLE)` — no shell involved |
| S2 | `sound_player.py` | Sound name received over local UDP/TCP socket was used directly to build file paths, enabling path traversal (e.g. `../../etc/passwd`) | Added `_is_safe_sound_name()` validation; names must match `^[A-Za-z0-9_\-]{1,128}$` |
| S3 | `sort.py` | `sys.argv[1] not in "123456"` used substring matching instead of set membership, so `"12"` would pass | Changed to `sys.argv[1] not in ("1","2","3","4","5","6")` |

## Reporting a vulnerability

Please open a GitHub issue tagged **[security]** or contact the maintainer
directly. Do not publicly disclose security issues before they are fixed.
