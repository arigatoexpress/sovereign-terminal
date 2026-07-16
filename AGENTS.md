# Agent Charter — sovereign-terminal

## Purpose
Mac-side CLI for the sovereign local agentic stack (`sov`, `ai`).

## Quick start
- `bin/ai` — main entrypoint (doctor, worker, ide, model, knowledge, etc.)
- `lib/ai_lib.py` — shared helpers
- `models/registry.yaml` — gateway-first model roster
- `recipes/` — reusable shell recipes

## Safety boundaries
- This repo orchestrates local-only tools. Do not start outward gateways (Hermes, Telegram, email) from here.
- Commands that touch model APIs should respect `models/registry.yaml` ordering and local-first defaults.
- Keep secrets in environment variables / Keychain; never commit credentials.

## Conventions
- Python 3.11+ for `lib/`.
- Shell scripts in `bin/` and `recipes/` must be macOS/Bash-compatible.
- YAML changes must be valid and loadable by the registry parser.
