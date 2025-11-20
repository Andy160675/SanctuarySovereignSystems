import os
from pathlib import Path
import random

INBOX = Path("Evidence/Inbox")
INBOX.mkdir(parents=True, exist_ok=True)

samples = [
    ("receipt_blurry_date.txt", "Receipt\nDate: [BLURRY]\nTotal: $50.00"),
    ("contract_no_total.txt", "Contract\nParties: A and B\nLine Item 1: $100\nLine Item 2: $200"),
    ("invoice_perfect.txt", "Invoice\nDate: 2025-11-20\nTotal: $500.00\nInv Date: 2025-11-20"),
    ("receipt_good.txt", "Receipt\nDate: 2025-11-19\nTotal: $12.50"),
    ("contract_good.txt", "Contract\nGrand Total: $10,000.00\nDate: 2025-01-01")
]

print(f"Seeding Batch 2 into {INBOX}...")
for name, content in samples:
    (INBOX / name).write_text(content)
    print(f" + {name}")

print("Batch 2 Seeded.")
