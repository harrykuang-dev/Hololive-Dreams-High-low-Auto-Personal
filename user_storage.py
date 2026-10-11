"""Per-user Windows data with lossless migration from older EXE folders."""
import json
import os
from pathlib import Path
import tempfile


def user_data_dir():
    local = os.environ.get('LOCALAPPDATA')
    return (Path(local) if local else Path.home()/'AppData'/'Local')/'HololiveDreamsHighLowAuto'


USER_DATA_DIR = user_data_dir()


def migrate_file(source, destination):
    """Move bytes only after an atomic, verified copy; never replace new data."""
    if not source.is_file() or destination.exists():
        return
    payload = source.read_bytes()
    if not isinstance(json.loads(payload), dict):
        raise ValueError(f'Invalid data file: {source}')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=destination.name+'.',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if temporary.read_bytes() != payload:
            raise OSError(f'Cannot verify copied data: {source}')
        # Hard-link publication is atomic and fails if another instance has
        # already created the destination. Both paths are on the same volume.
        try:
            os.link(temporary, destination)
        except FileExistsError:
            return
        if destination.read_bytes() != payload:
            raise OSError(f'Cannot verify migrated data: {source}')
        # If an older instance updated the file meanwhile, keep its record.
        if source.read_bytes() == payload:
            try:
                source.unlink()
            except OSError:
                pass  # Read-only old folders must not prevent the new app running.
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def prepare_user_data(legacy_dir, *, directory=None):
    directory = USER_DATA_DIR if directory is None else Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('daily_coins.json', 'settings.json'):
        destination=directory/filename
        if destination.exists() and not isinstance(json.loads(destination.read_bytes()),dict):
            raise ValueError(f'Invalid data file: {destination}')
    for filename in ('daily_coins.json', 'settings.json'):
        migrate_file(Path(legacy_dir)/filename, directory/filename)
    return directory
