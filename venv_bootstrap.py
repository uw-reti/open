"""Use a project-local .venv when it works on this machine; otherwise set one up or continue as-is."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def local_venv_python(project_root: Path) -> Path:
    if sys.platform == "win32":
        return project_root / ".venv" / "Scripts" / "python.exe"
    return project_root / ".venv" / "bin" / "python"


def _pyvenv_home_missing(project_root: Path) -> bool:
    cfg = project_root / ".venv" / "pyvenv.cfg"
    if not cfg.is_file():
        return False
    for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("home = "):
            home = line.split("=", 1)[1].strip()
            return bool(home) and not Path(home).exists()
    return False


def venv_is_runnable(venv_python: Path) -> bool:
    if not venv_python.is_file():
        return False
    try:
        r = subprocess.run(
            [str(venv_python), "-c", "import numpy, pandas"],
            capture_output=True,
            timeout=60,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def ensure_local_venv(project_root: Path) -> Path | None:
    """Create or repair .venv on this machine. Returns venv python path, or None on failure."""
    req = project_root / "requirements.txt"
    if not req.is_file():
        return None

    venv_python = local_venv_python(project_root)
    venv_dir = project_root / ".venv"

    if venv_dir.exists() and (_pyvenv_home_missing(project_root) or not venv_is_runnable(venv_python)):
        shutil.rmtree(venv_dir, ignore_errors=True)

    if not venv_is_runnable(venv_python):
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        subprocess.check_call(
            [str(local_venv_python(project_root)), "-m", "pip", "install", "-r", str(req)],
            cwd=str(project_root),
        )
        venv_python = local_venv_python(project_root)

    return venv_python if venv_is_runnable(venv_python) else None


def maybe_reexec_with_venv(script_path: Path) -> None:
    """Re-run the script under .venv when that environment is valid on this computer."""
    project_root = script_path.resolve().parent
    venv_python = ensure_local_venv(project_root)
    if venv_python is None:
        return

    try:
        wrong_interpreter = Path(sys.executable).resolve() != venv_python.resolve()
    except OSError:
        wrong_interpreter = True

    if wrong_interpreter:
        rc = subprocess.call([str(venv_python), str(script_path), *sys.argv[1:]])
        raise SystemExit(rc)
