# -*- coding: utf-8 -*-
"""
Configuration for the Boardroom governance layer.

These settings control automation behavior, safe mode restrictions,
and external anchoring behavior.
"""

import os

# =============================================================================
# PUBLIC SAFE MODE
# =============================================================================
# When True, restricts automation and disables external anchoring.
# Use for public deployments or untrusted environments.

PUBLIC_SAFE_MODE = os.getenv("PUBLIC_SAFE_MODE", "false").lower() == "true"

# Block ALL automation when in public safe mode
BLOCK_AUTOMATION_IN_PUBLIC_SAFE_MODE = os.getenv(
    "BLOCK_AUTOMATION_IN_PUBLIC_SAFE_MODE", "false"
).lower() == "true"

# Actions allowed even in public safe mode
# VERIFY_CHAIN_NOW is safe - it only reads and validates
SAFE_ALLOWED_HANDLERS = set(
    os.getenv("SAFE_ALLOWED_HANDLERS", "VERIFY_CHAIN_NOW").split(",")
)

# =============================================================================
# EXTERNAL ANCHORING
# =============================================================================
# Disable external anchoring (RFC3161, IPFS, Arweave) in safe mode or test

DISABLE_EXTERNAL_ANCHOR = os.getenv("DISABLE_EXTERNAL_ANCHOR", "false").lower() == "true"

# If PUBLIC_SAFE_MODE is on, automatically disable external anchoring
if PUBLIC_SAFE_MODE:
    DISABLE_EXTERNAL_ANCHOR = True
