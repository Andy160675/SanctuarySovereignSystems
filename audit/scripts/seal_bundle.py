import hashlib
import os
import argparse
from datetime import datetime

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def seal_bundle(input_bundle, output_file):
    if not os.path.exists(input_bundle):
        print(f"Error: Bundle {input_bundle} not found.")
        return

    checksum = calculate_sha256(input_bundle)
    
    with open(output_file, "w") as f:
        f.write(f"BUNDLE_NAME: {os.path.basename(input_bundle)}\n")
        f.write(f"SEAL_TIME: {datetime.now().isoformat()}\n")
        f.write(f"SHA256: {checksum}\n")
    
    print(f"Bundle {input_bundle} sealed.")
    print(f"Merkle Root (SHA256): {checksum}")
    print(f"Result written to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seal an audit bundle with a SHA256 Merkle root.")
    parser.add_argument("--input", required=True, help="Path to the audit bundle (tar.gz or zip)")
    parser.add_argument("--output", required=True, help="Path to the output Merkle root file")
    parser.add_argument("--algorithm", default="sha256", help="Hashing algorithm (default: sha256)")
    
    args = parser.parse_args()
    
    if args.algorithm.lower() != "sha256":
        print("Currently only sha256 is supported.")
    
    seal_bundle(args.input, args.output)
