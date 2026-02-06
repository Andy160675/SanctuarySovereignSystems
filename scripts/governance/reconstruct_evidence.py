import hashlib
import os
import sys

def compute_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()

def verify_case(case_file):
    print(f"--- Reconstructing Evidence for {case_file} ---")
    case_id = os.path.basename(case_file).split("_")[1].split(".")[0]
    evidence_dir = f"evidence/proof_cases/CASE_{case_id}"
    
    if not os.path.exists(evidence_dir):
        print(f"ERROR: Evidence directory {evidence_dir} not found.")
        return False

    with open(f"{evidence_dir}/pre_state.json", "r") as f: pre_data = f.read()
    with open(f"{evidence_dir}/post_state.json", "r") as f: post_data = f.read()
    with open(f"{evidence_dir}/evaluation.json", "r") as f: eval_data = f.read()

    pre_hash = compute_hash(pre_data)
    post_hash = compute_hash(post_data)
    eval_hash = compute_hash(eval_data)

    # Read the markdown case to compare
    with open(case_file, "r", encoding="utf-8") as f:
        content = f.read()

    success = True
    if pre_hash not in content:
        print(f"FAIL: Pre-state hash mismatch!")
        success = False
    else:
        print(f"PASS: Pre-state hash verified: {pre_hash}")

    if eval_hash not in content:
        print(f"FAIL: Constitutional Evaluation hash mismatch!")
        success = False
    else:
        print(f"PASS: Evaluation hash verified: {eval_hash}")

    if post_hash not in content:
        print(f"FAIL: Post-state hash mismatch!")
        success = False
    else:
        print(f"PASS: Post-state hash verified: {post_hash}")

    if success:
        print(f"RESULT: Case {case_id} Reconstruction SUCCESSFUL.")
    else:
        print(f"RESULT: Case {case_id} Reconstruction FAILED.")
    
    return success

def main():
    if len(sys.argv) > 1:
        verify_case(sys.argv[1])
    else:
        # Verify all cases in scenarios/proof_cases/
        cases = [f for f in os.listdir("scenarios/proof_cases") if f.endswith(".md")]
        all_success = True
        for case in sorted(cases):
            if not verify_case(f"scenarios/proof_cases/{case}"):
                all_success = False
            print()
        
        if all_success:
            print("=== ALL PROOF CASES VERIFIED SUCCESSFULLY ===")
            sys.exit(0)
        else:
            print("=== SOME PROOF CASES FAILED VERIFICATION ===")
            sys.exit(1)

if __name__ == "__main__":
    main()
