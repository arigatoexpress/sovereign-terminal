#!/usr/bin/env python3
"""
ai_lib.py — shared utilities for the sovereign `ai` CLI.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

AI_HOME = Path.home() / ".ai"
REGISTRY_PATH = AI_HOME / "models" / "registry.yaml"
VAULT_PATH = Path(os.environ.get("KNOWLEDGE_VAULT", Path.home() / "Knowledge"))


def load_registry() -> dict:
    import yaml

    if not REGISTRY_PATH.exists():
        return {}
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f) or {}


def resolve_alias(name: str, registry: Optional[dict] = None) -> str:
    """Resolve a model alias (fast, deep, editor) to a concrete model name."""
    if "/" in name:
        return name
    registry = registry or load_registry()
    aliases = registry.get("aliases", {})
    if name in aliases:
        return aliases[name]
    local_models = registry.get("local", {}).get("models", {})
    if name in local_models:
        return f"ollama/{name}"
    cloud_models = registry.get("cloud", {})
    if name in cloud_models:
        return f"anthropic/{name}" if cloud_models[name].get("provider") == "anthropic" else name
    return name


def guard_check(cmd: str) -> tuple[str, Optional[str]]:
    """Run guard-bash.sh guard-check on a command string. Returns (allow|deny|ask, reason)."""
    guard_script = Path.home() / ".aider" / "guard-bash.sh"
    if not guard_script.exists():
        return ("allow", "guard script not found")
    proc = subprocess.run(
        ["bash", "-c", f'source "{guard_script}" && guard-check {shlex_quote(cmd)}; echo "EXIT:$?"'],
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    m = re.search(r"EXIT:(\d+)", out)
    code = int(m.group(1)) if m else 0
    reason = re.sub(r"EXIT:\d+", "", out).strip()
    if code == 1:
        return ("deny", reason or "guard rule denied")
    if code == 2:
        return ("ask", reason or "guard rule requires approval")
    return ("allow", reason)


def shlex_quote(s: str) -> str:
    import shlex

    return shlex.quote(s)


def log_session(tool: str, args: list[str], outcome: str) -> None:
    """Append a minimal session log entry."""
    from datetime import datetime, timezone

    log_dir = AI_HOME / "sessions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "args": args,
        "outcome": outcome,
    }
    import json

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def ensure_ollama() -> bool:
    """Check that Ollama is reachable."""
    import urllib.request

    try:
        urllib.request.urlopen("http://127.0.0.1:11434", timeout=3)
        return True
    except Exception:
        return False
