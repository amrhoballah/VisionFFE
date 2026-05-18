#!/usr/bin/env python3
"""One-shot env diagnostic for arch/venv mismatches. Writes NDJSON to debug log."""
import json
import os
import platform
import subprocess
import sys
import time

LOG_PATH = "/Users/amrhoballah/Documents/GitHub/VisionFFE/.cursor/debug-031ffc.log"
SESSION_ID = "031ffc"
RUN_ID = os.environ.get("DEBUG_RUN_ID", "pre-fix")


def log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    entry = {
        "sessionId": SESSION_ID,
        "runId": RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # #endregion


def file_arch(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    try:
        out = subprocess.check_output(["file", path], text=True).strip()
        if "arm64" in out:
            return "arm64"
        if "x86_64" in out:
            return "x86_64"
        return out
    except Exception as e:
        return f"error:{e}"


def main() -> None:
    # H1: wrong interpreter (system vs venv)
    log("H1", "debug_python_env.py:main", "python executable", {
        "executable": sys.executable,
        "prefix": sys.prefix,
        "base_prefix": getattr(sys, "base_prefix", ""),
        "in_venv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
    })

    # H2: process arch vs wheel arch
    log("H2", "debug_python_env.py:main", "platform", {
        "machine": platform.machine(),
        "platform": platform.platform(),
    })

    pydantic_core_so = None
    pydantic_import_ok = False
    pydantic_error = None
    try:
        import pydantic_core  # noqa: F401
        pydantic_core_so = getattr(pydantic_core, "__file__", None)
        pydantic_import_ok = True
    except Exception as e:
        pydantic_error = repr(e)

    # H3: pydantic_core binary architecture
    log("H3", "debug_python_env.py:main", "pydantic_core", {
        "import_ok": pydantic_import_ok,
        "so_path": pydantic_core_so,
        "so_arch": file_arch(pydantic_core_so) if pydantic_core_so else None,
        "error": pydantic_error,
    })

    # H4: which uvicorn on PATH vs venv
    which_uvicorn = subprocess.run(
        ["which", "uvicorn"], capture_output=True, text=True
    ).stdout.strip() or None
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    venv_uvicorn = os.path.join(repo_root, ".venv", "bin", "uvicorn")
    log("H4", "debug_python_env.py:main", "uvicorn resolution", {
        "which_uvicorn": which_uvicorn,
        "venv_uvicorn_exists": os.path.isfile(venv_uvicorn),
        "venv_uvicorn_arch": file_arch(venv_uvicorn) if os.path.isfile(venv_uvicorn) else None,
    })

    # H5: fastapi import (same failure as uvicorn load)
    fastapi_ok = False
    fastapi_error = None
    try:
        import fastapi  # noqa: F401
        fastapi_ok = True
    except Exception as e:
        fastapi_error = repr(e)
    log("H5", "debug_python_env.py:main", "fastapi import", {
        "ok": fastapi_ok,
        "error": fastapi_error,
    })


if __name__ == "__main__":
    main()
