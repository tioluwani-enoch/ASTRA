"""
Filesystem execution layer.

This is the ONLY place in Astra that touches the filesystem for user-created files.
All paths are sandboxed inside data/files/ — no arbitrary path traversal allowed.
"""
from pathlib import Path

from config.constants import DATA_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

FILES_DIR = DATA_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

# Allowed extensions — explicit allowlist, not a blocklist
_ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".csv"}


def _safe_path(filename: str) -> Path:
    """
    Resolve filename to an absolute path inside FILES_DIR.
    Raises ValueError if the resolved path escapes the sandbox.
    """
    path = (FILES_DIR / filename).resolve()
    if not str(path).startswith(str(FILES_DIR.resolve())):
        raise ValueError(f"Path traversal attempt blocked: {filename!r}")
    suffix = path.suffix.lower()
    if suffix and suffix not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed: {suffix!r}. Allowed: {_ALLOWED_EXTENSIONS}")
    return path


def create_file(filename: str, content: str) -> Path:
    """Write a new file. Raises FileExistsError if it already exists."""
    path = _safe_path(filename)
    if path.exists():
        raise FileExistsError(f"{filename!r} already exists. Use update_file to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info(f"[FILES] Created: {path}")
    return path


def read_file(filename: str) -> str:
    """Read and return file content. Raises FileNotFoundError if missing."""
    path = _safe_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"{filename!r} not found in files store.")
    content = path.read_text(encoding="utf-8")
    logger.info(f"[FILES] Read: {path}")
    return content


def update_file(filename: str, content: str) -> Path:
    """Overwrite an existing file. Raises FileNotFoundError if it doesn't exist."""
    path = _safe_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"{filename!r} not found. Use create_file to create it first.")
    path.write_text(content, encoding="utf-8")
    logger.info(f"[FILES] Updated: {path}")
    return path


def list_files() -> list[str]:
    """Return filenames of all files in the store."""
    return [f.name for f in FILES_DIR.iterdir() if f.is_file()]
