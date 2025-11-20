import os
from pathlib import Path

INBOX = Path("Evidence/Inbox")
INBOX.mkdir(parents=True, exist_ok=True)

print(f"🌱 Seeding {INBOX} with dummy evidence...")
for i in range(1, 16):
    file_path = INBOX / f"invoice_sample_{i:03d}.txt"
    file_path.write_text(f"Dummy Invoice Content {i}")

print(f"✅ Created 15 sample files.")
