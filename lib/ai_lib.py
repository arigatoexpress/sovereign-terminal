#!/usr/bin/env python3
"""
ai_lib.py — shared utilities for the sovereign `ai` CLI.

Model plane (2026-07-20): registry.yaml RETIRED. Aliases and local model names
are explicit here. Consumers (aider, hermes, gpu) own their own defaults;
this map is only for the `ai` CLI role shortcuts. Gateway stays a pure
byte-forwarder — unknown models 404 at Ollama.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

AI_HOME = Path.home() / ".ai"
# Historical path — kept only so load_registry can report retirement.
REGISTRY_PATH = AI_HOME / "models" / "registry.yaml"
REGISTRY_RETIRED_PATH = AI_HOME / "models" / "registry.yaml.retired"
VAULT_PATH = Path(os.environ.get("KNOWLEDGE_VAULT", Path.home() / "Knowledge"))

# Explicit role → concrete Ollama model (no central SoT file).
ALIASES: dict[str, str] = {
    "default": "qwen2.5-coder:14b",
    "code": "qwen2.5-coder:14b",
    "coder": "codestral:22b",
    "editor": "qwen2.5-coder:14b",
    "speed": "gpt-oss:20b",
    "agent": "qwen3-coder:30b",
    "gen": "qwen3:14b",
    "fast": "qwen3:4b",
    "reason": "deepseek-r1:14b",
    "deep": "deepseek-r1:14b",
    "weak": "gemma3:4b",
    "chat": "dolphin3:latest",
    "embed": "mxbai-embed-large:latest",
    "cloud": "anthropic/claude-sonnet-5",
}

# Known local model ids (for ollama/ prefix resolution). Not a health roster.
LOCAL_MODELS: frozenset[str] = frozenset({
    "codestral:22b",
    "qwen2.5-coder:14b",
    "qwen3:14b",
    "qwen3-coder:30b",
    "gpt-oss:20b",
    "gemma3:4b",
    "gemma4:12b",
    "qwen3-vl:8b",
    "devstral:24b",
    "deepseek-r1:14b",
    "deepseek-r1:8b",
    "qwen3:4b",
    "dolphin3:latest",
    "mxbai-embed-large:latest",
    "nomic-embed-text:latest",
})


def load_registry() -> dict:
    """Backward-compatible shape for callers that still expect a registry dict.

    Does NOT read registry.yaml (retired). Returns the explicit in-code map.
    """
    return {
        "aliases": dict(ALIASES),
        "local": {
            "base_url": "http://127.0.0.1:8800/v1",
            "default": ALIASES["default"],
            "models": {m: {"provider": "ollama", "name": m} for m in sorted(LOCAL_MODELS)},
        },
        "retired": True,
        "source": "ai_lib.ALIASES",
    }


def resolve_alias(name: str, registry: Optional[dict] = None) -> str:
    """Resolve a model alias (fast, deep, editor) to a concrete model name."""
    if "/" in name:
        return name
    aliases = (registry or load_registry()).get("aliases", ALIASES)
    if name in aliases:
        target = aliases[name]
        if "/" in target:
            return target
        if target in LOCAL_MODELS or ":" in target:
            return f"ollama/{target}" if not target.startswith("ollama/") else target
        return target
    if name in LOCAL_MODELS:
        return f"ollama/{name}"
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
