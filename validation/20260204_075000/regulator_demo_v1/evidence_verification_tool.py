import json
import hashlib

def verify_evidence(evidence):
    evidence_copy = evidence.copy()
    received_hash = evidence_copy.pop('evidence_hash', None)
    if not received_hash:
        return False, "No hash found"
    
    encoded = json.dumps(evidence_copy, sort_keys=True).encode()
    calculated_hash = f"SHA256:{hashlib.sha256(encoded).hexdigest()}"
    
    if received_hash == calculated_hash:
        return True, calculated_hash
    else:
        return False, f"Hash mismatch! Expected {calculated_hash}, got {received_hash}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python evidence_verification_tool.py <scenario.json>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
        is_valid, msg = verify_evidence(data['evidence_chain_fragment'])
        print(f"Verification Result: {'PASS' if is_valid else 'FAIL'}")
        print(f"Detail: {msg}")
