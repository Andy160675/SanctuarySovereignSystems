import unittest
import hashlib
import os

class TestAutonomyLimitsHashGuard(unittest.TestCase):
    def test_law_file_integrity(self):
        """Verifies that AUTONOMY_LIMITS.md matches the approved anchor hash."""
        approved_hash = "d5d79cfd57fa1226ad5fdb3c76e5b8917a843a93a1c1774d7d2b44784861ed92"
        file_path = "AUTONOMY_LIMITS.md"
        
        if not os.path.exists(file_path):
            self.fail(f"{file_path} missing")
            
        with open(file_path, 'rb') as f:
            current_hash = hashlib.sha256(f.read()).hexdigest().lower()
            
        self.assertEqual(current_hash, approved_hash, "AUTONOMY_LIMITS.md hash mismatch! Unauthorized change detected.")

if __name__ == "__main__":
    unittest.main()
