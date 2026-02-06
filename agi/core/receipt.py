# agi/core/receipt.py
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).resolve().parent / "sovereign_model.sqlite"
RECEIPTS_DIR = Path(__file__).resolve().parent / "receipts"
RECEIPTS_DIR.mkdir(exist_ok=True)

@dataclass
class SovereignReceipt:
    receipt_id: str
    answer_id: str
    model_id: str
    policy_version: str
    mode: str  # "raw" | "explained"
    agent_path: List[str]
    prompt_hash: str
    answer_hash: str
    interpreter_prompt_hash: Optional[str] = None
    assistant_system_prompt_hash: Optional[str] = None
    parent_receipt_id: Optional[str] = None
    drift_detected: bool = False
    drift_details: Optional[List[Dict]] = None
    timestamp: int = int(time.time())

def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Base table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sovereign_answers (
            answer_id TEXT PRIMARY KEY,
            receipt_id TEXT NOT NULL,
            question TEXT NOT NULL,
            raw_answer TEXT NOT NULL,
            explained_answer TEXT,
            audit_receipt TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # Assistant messages table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS assistant_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answer_id TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            role TEXT NOT NULL,        -- "user" | "assistant"
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (answer_id) REFERENCES sovereign_answers(answer_id)
        )
        """
    )
    # Migration: ensure audit_receipt column exists (older schema compatibility)
    if not _column_exists(cur, "sovereign_answers", "audit_receipt"):
        cur.execute("ALTER TABLE sovereign_answers ADD COLUMN audit_receipt TEXT")
    conn.commit()
    conn.close()

def write_receipt_json(receipt: SovereignReceipt) -> Path:
    path = RECEIPTS_DIR / f"{receipt.receipt_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(receipt), f, indent=2, ensure_ascii=False)
    return path

def store_answer_and_receipt(
    receipt: SovereignReceipt,
    question: str,
    raw_answer: str,
    explained_answer: Optional[str] = None,
    audit_receipt: Optional[Dict[str, Any]] = None,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    audit_json = json.dumps(audit_receipt, ensure_ascii=False) if audit_receipt is not None else None
    cur.execute(
        """
        INSERT OR REPLACE INTO sovereign_answers
            (answer_id, receipt_id, question, raw_answer, explained_answer, audit_receipt, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            receipt.answer_id,
            receipt.receipt_id,
            question,
            raw_answer,
            explained_answer,
            audit_json,
            now,
        ),
    )
    conn.commit()
    conn.close()

def store_assistant_message(answer_id: str, receipt_id: str, role: str, message: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cur.execute(
        """
        INSERT INTO assistant_messages
            (answer_id, receipt_id, role, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (answer_id, receipt_id, role, message, now),
    )
    conn.commit()
    conn.close()
