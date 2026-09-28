"""Self-update: pull the latest code from the GitHub repo and restart.

The version marker is the latest commit SHA on `main`, read cheaply from the
commits Atom feed (no API rate limit). When it changes, the package files are
replaced from the repo zip and the agent re-executes itself. A checkout that
contains a .git folder (i.e. a dev tree) is skipped, so this never overwrites
the source you are editing.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile

from . import config as cfgmod

_SHA_FILE = cfgmod.CONFIG_DIR / "update_sha.txt"


def _repo(cfg: dict) -> str:
    return cfg.get("repo") or "matif-dev/madratif"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "madratif-updater"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read()


def _load_sha():
    try:
        return _SHA_FILE.read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def _save_sha(sha: str) -> None:
    try:
        cfgmod.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _SHA_FILE.write_text(sha, encoding="utf-8")
    except Exception:
        pass


def _is_dev_checkout() -> bool:
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(d, ".git")):
            return True
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return False


def remote_sha(cfg: dict):
    try:
        text = _get(f"https://github.com/{_repo(cfg)}/commits/main.atom").decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r"Commit/([0-9a-f]{7,40})", text)
    return m.group(1) if m else None


def apply_update(cfg: dict, pkg_dir: str | None = None) -> None:
    if pkg_dir is None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
    repo = _repo(cfg)
    name = repo.split("/")[-1]
    data = _get(f"https://codeload.github.com/{repo}/zip/refs/heads/main")
    tmp = tempfile.mkdtemp(prefix="madratif-upd-")
    try:
        zpath = os.path.join(tmp, "src.zip")
        with open(zpath, "wb") as fh:
            fh.write(data)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(tmp)
        new_pkg = os.path.join(tmp, f"{name}-main", "src", "madratif")
        if not os.path.isdir(new_pkg):
            raise RuntimeError("struktur repo tidak sesuai")
        new_names = set()
        for fn in os.listdir(new_pkg):
            if fn.endswith(".py"):
                shutil.copy2(os.path.join(new_pkg, fn), os.path.join(pkg_dir, fn))
                new_names.add(fn)
        for fn in os.listdir(pkg_dir):
            if fn.endswith(".py") and fn not in new_names:
                try:
                    os.remove(os.path.join(pkg_dir, fn))
                except OSError:
                    pass
        shutil.rmtree(os.path.join(pkg_dir, "__pycache__"), ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_and_apply(cfg: dict, force: bool = False, pkg_dir: str | None = None):
    """Returns (updated: bool, message: str)."""
    if _is_dev_checkout():
        return False, "mode dev (update dilewati)"
    sha = remote_sha(cfg)
    stored = _load_sha()
    if not force:
        if sha is None:
            return False, "cek update gagal"
        if stored is None:
            _save_sha(sha)
            return False, "baseline disimpan"
        if sha == stored:
            return False, "sudah terbaru"
    elif sha and stored and sha == stored:
        return False, "sudah versi terbaru"

    apply_update(cfg, pkg_dir)
    if sha:
        _save_sha(sha)
    return True, "diperbarui" + (f" ke {sha[:8]}" if sha else "")


def restart() -> None:
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os.execv(sys.executable, [sys.executable, "-m", "madratif"] + sys.argv[1:])
