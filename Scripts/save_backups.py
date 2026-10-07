"""Keep complete, portable snapshots of the game's persistent data."""
from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar
import tempfile
import time
import zipfile
import json
from datetime import datetime, timezone

_transactions = ContextVar('save_backup_transactions', default=None)


@contextmanager
def backup_transaction(root):
    """Keep one pre-operation snapshot for a group of related file changes."""
    key = str(Path(root).resolve())
    current = _transactions.get() or {}
    if key in current:
        yield
        return
    token = _transactions.set({**current, key: {'captured': False}})
    try:
        yield
    finally:
        _transactions.reset(token)


def trim_backups(root, count):
    directory = Path(root) / 'Settings' / 'Backups'
    archives = sorted(directory.glob('save-*.zip'), key=lambda archive: archive.stat().st_mtime_ns, reverse=True)
    for archive in archives[max(0, int(count)):]:
        archive.unlink()


def backup_before_write(root, path, value, count):
    """Archive the previous state before changing a save file."""
    root, path = Path(root).resolve(), Path(path).resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return
    if not relative.parts or relative.parts[0] not in {'Player', 'Items', 'Settings'}:
        return
    if 'Backups' in relative.parts or path.suffix != '.txt':
        return
    if path.exists() and path.read_bytes() == str(value).encode('utf-8'):
        return
    if not path.exists() and not all(
        (root / file).exists() for file in ('Player/data.txt', 'Settings/settings.txt')
    ):
        return
    count = max(0, int(count))
    if not count:
        return
    transaction = (_transactions.get() or {}).get(str(root))
    if transaction is not None and transaction['captured']:
        return
    create_backup(root)
    if transaction is not None:
        transaction['captured'] = True
    trim_backups(root, count)


def create_backup(root, name="", manual=False):
    root = Path(root).resolve()
    directory = root / 'Settings' / 'Backups'
    directory.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    kind = 'manual' if manual else 'save'
    # the chosen name stays inside the zip, filenames always use the timestamp
    stamp = created.strftime('%Y-%m-%d_%H-%M-%S')
    destination = directory / f'{kind}-{stamp}-{time.time_ns()}.zip'
    metadata = {
        'name': str(name).strip(),
        'kind': 'manual' if manual else 'automatic',
        'created_at': created.isoformat(),
        'created_at_local': created.astimezone().isoformat(),
        'format_version': 1,
    }
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('backup.json', json.dumps(metadata, indent=4, ensure_ascii=False))
            for folder in ('Player', 'Items', 'Settings'):
                for source in sorted((root / folder).rglob('*.txt')):
                    if source.is_file() and 'Backups' not in source.relative_to(root).parts:
                        archive.write(source, source.relative_to(root))
        temporary.replace(destination)
        return destination
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
