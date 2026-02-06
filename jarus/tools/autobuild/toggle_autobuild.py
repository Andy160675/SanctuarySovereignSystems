#!/usr/bin/env python3
"""
Autobuild Toggle CLI
====================
Passcode-gated control for enabling/disabling autobuild.

Usage:
    python toggle_autobuild.py status
    python toggle_autobuild.py enable --passcode <code> --who <operator>
    python toggle_autobuild.py disable --passcode <code> --who <operator>
    python toggle_autobuild.py check  # For CI/scripts - exits 0 if enabled, 1 if not
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import click
except ImportError:
    print("ERROR: click module not found. Install with: pip install click")
    sys.exit(1)


# Configuration
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "autobuild.json"


def load_config() -> dict:
    """Load autobuild configuration."""
    if not CONFIG_PATH.exists():
        raise click.ClickException(f"Config not found: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    """Save autobuild configuration."""
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, sort_keys=False)


def hash_passcode(passcode: str) -> str:
    """Hash passcode using SHA-256."""
    return hashlib.sha256(passcode.encode("utf-8")).hexdigest()


def require_passcode(passcode: str, cfg: dict) -> None:
    """Verify passcode against stored hash."""
    if hash_passcode(passcode) != cfg.get("passcode_hash"):
        raise click.ClickException("Invalid passcode.")


@click.group()
def cli():
    """Autobuild passcode gate - controls system build authorization."""
    pass


@cli.command("status")
def status():
    """Show current autobuild status."""
    cfg = load_config()
    state = "ENABLED" if cfg.get("enabled") else "DISABLED"
    click.echo(f"Autobuild: {state}")
    if cfg.get("last_changed_at_utc"):
        click.echo(
            f"Last changed at {cfg['last_changed_at_utc']} "
            f"by {cfg.get('last_changed_by') or 'unknown'}"
        )


@cli.command("enable")
@click.option("--passcode", prompt=True, hide_input=True, confirmation_prompt=False,
              help="Authorization passcode")
@click.option("--who", default="unknown", help="Identifier of the operator")
def enable(passcode: str, who: str):
    """Enable autobuild (passcode required)."""
    cfg = load_config()
    require_passcode(passcode, cfg)
    cfg["enabled"] = True
    cfg["last_changed_by"] = who
    cfg["last_changed_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_config(cfg)
    click.echo("Autobuild ENABLED.")


@cli.command("disable")
@click.option("--passcode", prompt=True, hide_input=True, confirmation_prompt=False,
              help="Authorization passcode")
@click.option("--who", default="unknown", help="Identifier of the operator")
def disable(passcode: str, who: str):
    """Disable autobuild (passcode required)."""
    cfg = load_config()
    require_passcode(passcode, cfg)
    cfg["enabled"] = False
    cfg["last_changed_by"] = who
    cfg["last_changed_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_config(cfg)
    click.echo("Autobuild DISABLED.")


@cli.command("check")
def check():
    """Exit 0 if autobuild enabled, 1 otherwise (for CI/scripts)."""
    cfg = load_config()
    if cfg.get("enabled"):
        click.echo("Autobuild: ENABLED")
        raise SystemExit(0)
    else:
        click.echo("Autobuild: DISABLED")
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
