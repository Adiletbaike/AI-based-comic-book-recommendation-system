#!/usr/bin/env python3
"""
Dev runner for this repo.

What it does:
  - Ensures backend venv exists at backend/.venv
  - Installs backend deps when backend/requirements.txt changes
  - Ensures backend/.env exists and has >=32-byte SECRET_KEY/JWT_SECRET_KEY
  - Starts backend dev server and keeps it running
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
BACKEND_VENV = BACKEND_DIR / ".venv"
BACKEND_VENV_PY = BACKEND_VENV / "bin" / "python"


def _pick_backend_python() -> str:
    # Avoid creating a backend venv with the system default python (often 3.14+ on this machine),
    # because key ML deps (tokenizers) may not have wheels yet.
    for cand in ("python3.11", "python3.12", "python3"):
        p = shutil.which(cand)
        if p:
            return p
    return sys.executable


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


def _ensure_backend_venv() -> None:
    if BACKEND_VENV_PY.exists():
        return
    py = _pick_backend_python()
    print(f"[dev] creating backend venv at {BACKEND_VENV} using {py}")
    _run([py, "-m", "venv", str(BACKEND_VENV)], cwd=BACKEND_DIR)


def _ensure_backend_deps() -> None:
    req = BACKEND_DIR / "requirements.txt"
    stamp = BACKEND_VENV / ".requirements.sha256"
    want = _sha256_file(req)
    have = stamp.read_text().strip() if stamp.exists() else ""

    if want == have:
        return

    print("[dev] installing backend deps (requirements changed)")
    try:
        _run([str(BACKEND_VENV_PY), "-m", "pip", "install", "-r", str(req)], cwd=BACKEND_DIR)
    except subprocess.CalledProcessError:
        # If the venv has an incompatible lock of packages, recreate it from scratch.
        print("[dev] backend deps install failed; recreating venv and retrying")
        try:
            shutil.rmtree(BACKEND_VENV)
        except Exception:
            pass
        _ensure_backend_venv()
        _run([str(BACKEND_VENV_PY), "-m", "pip", "install", "-r", str(req)], cwd=BACKEND_DIR)
    stamp.write_text(want)


def _upsert_env_line(text: str, key: str, value: str) -> str:
    if re.search(rf"^{re.escape(key)}=.*$", text, flags=re.M):
        return re.sub(rf"^{re.escape(key)}=.*$", f"{key}={value}", text, flags=re.M)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + f"{key}={value}\n"


def _ensure_backend_env() -> None:
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        example = BACKEND_DIR / ".env.example"
        if example.exists():
            env_path.write_text(example.read_text())
        else:
            env_path.write_text("")

    text = env_path.read_text()

    def _get(key: str) -> str | None:
        m = re.search(rf"^{re.escape(key)}=(.*)$", text, flags=re.M)
        return m.group(1).strip() if m else None

    def _needs_fix(v: str | None) -> bool:
        if not v:
            return True
        # jwt wants >= 32 bytes for HS256. Treat value length as bytes for ASCII-ish secrets.
        return len(v.encode("utf-8")) < 32

    if _needs_fix(_get("SECRET_KEY")):
        text = _upsert_env_line(text, "SECRET_KEY", secrets.token_hex(32))
    if _needs_fix(_get("JWT_SECRET_KEY")):
        text = _upsert_env_line(text, "JWT_SECRET_KEY", secrets.token_hex(32))

    env_path.write_text(text)


def main() -> int:
    os.chdir(REPO_ROOT)

    _ensure_backend_venv()
    _ensure_backend_deps()
    _ensure_backend_env()

    # Start backend
    backend_log = BACKEND_DIR / "dev.log"
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"
    print("[dev] starting backend")
    backend = subprocess.Popen(
        [str(BACKEND_VENV_PY), "run.py"],
        cwd=str(BACKEND_DIR),
        env=backend_env,
        stdout=backend_log.open("ab"),
        stderr=subprocess.STDOUT,
    )

    # Wait for backend to write .runtime-port (best-effort)
    port_file = BACKEND_DIR / ".runtime-port"
    for _ in range(100):
        if port_file.exists() and port_file.read_text().strip():
            break
        time.sleep(0.05)

    port = port_file.read_text().strip() if port_file.exists() else "5001"
    print("")
    print("[dev] running")
    print(f"[dev] backend:  http://127.0.0.1:{port}")
    print(f"[dev] logs:     {backend_log}")

    procs = [backend]

    def _shutdown(*_args):
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(0.2)
        for p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Keep running until backend exits
    while True:
        b = backend.poll()
        if b is not None:
            break
        time.sleep(0.25)

    _shutdown()
    if backend.returncode not in (None, 0):
        print(f"[dev] backend exited with code {backend.returncode}. See {backend_log}", file=sys.stderr)
        return backend.returncode or 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
