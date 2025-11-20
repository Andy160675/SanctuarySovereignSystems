import os
from pathlib import Path
import random

INBOX = Path("Evidence/Inbox")
INBOX.mkdir(parents=True, exist_ok=True)

samples = [
    ("receipt_faded_04.txt", "Receipt\nDate: [FADED]\nTotal: $50.00"),
    ("invoice_generic_02.txt", "Invoice\nTo: Cash Customer\nTotal: $200"),
    ("invoice_perfect_03.txt", "Invoice\nDate: 2025-11-20\nTotal: $500.00\nInv Date: 2025-11-20"),
    ("receipt_good_05.txt", "Receipt\nDate: 2025-11-19\nTotal: $12.50"),
    ("contract_good_02.txt", "Contract\nGrand Total: $10,000.00\nDate: 2025-01-01")
]

print(f"Seeding Batch 3 into {INBOX}...")
for name, content in samples:
    (INBOX / name).write_text(content)
    print(f" + {name}")

print("Batch 3 Seeded.")
