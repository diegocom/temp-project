import re
from pathlib import Path
from zipfile import ZipFile
import py7zr  # obbligatorio

_FORTIFY_PREFIX = "Fortify_SCA_and_Apps_"
_VERSION_RE = re.compile(rf"^{re.escape(_FORTIFY_PREFIX)}(\d+(?:\.\d+){2})$")


def _parse_version(name: str):
    """Estrae (major, minor, patch) da 'Fortify_SCA_and_Apps_X.Y.Z'."""
    m = _VERSION_RE.match(name)
    if not m:
        return None
    return tuple(int(p) for p in m.group(1).split("."))


def _find_latest(paths):
    """Trova il percorso con la versione più alta tra quelli che matchano il pattern."""
    best = None
    best_ver = None
    for p in paths:
        ver = _parse_version(p.name if p.is_dir() else p.stem)
        if ver and (best_ver is None or ver > best_ver):
            best_ver, best = ver, p
    return best


def _extract_zip(src_zip: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(src_zip, "r") as zf:
        zf.extractall(dest_dir)


def _extract_7z(src_7z: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(src_7z, mode="r") as zf:
        zf.extractall(path=dest_dir)


def ensure_fortify_dir(base_dir: Path | str = ".") -> Path:
    """
    Garantisce la presenza di una cartella Fortify_SCA_and_Apps_X.Y.Z.
    - Se esiste già, ritorna la più recente.
    - Se non esiste ma c’è un archivio .zip o .7z, lo estrae e ritorna la cartella.
    - Se non trova nulla, solleva FileNotFoundError.
    """
    base = Path(base_dir).resolve()

    # 1) Cerca cartelle già estratte
    candidate_dirs = [p for p in base.iterdir() if p.is_dir() and _parse_version(p.name)]
    latest_dir = _find_latest(candidate_dirs)
    if latest_dir:
        return latest_dir

    # 2) Cerca archivi
    archives = [p for p in base.iterdir() if p.suffix.lower() in {".zip", ".7z"} and _parse_version(p.stem)]
    latest_archive = _find_latest(archives)
    if not latest_archive:
        raise FileNotFoundError("Né cartelle né archivi Fortify_SCA_and_Apps_XX.X.X trovati.")

    dest = base / latest_archive.stem
    if latest_archive.suffix.lower() == ".zip":
        _extract_zip(latest_archive, dest)
    else:
        _extract_7z(latest_archive, dest)

    return dest
