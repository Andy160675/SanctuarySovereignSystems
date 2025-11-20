from typing import Dict, Tuple

def run_log_cleanup_simulation(params: Dict) -> Tuple[bool, Dict]:
    """
    A concrete task. 
    Returns: (success: bool, metrics: Dict)
    """
    print(f"   [TASK] Cleaning logs older than {params.get('days', 30)} days...")
    # In reality: boto3.client('s3').delete_objects(...)
    return True, {"freed_space_mb": 150, "files_deleted": 42}

def run_security_scan(params: Dict) -> Tuple[bool, Dict]:
    """
    Another concrete task.
    """
    print(f"   [TASK] Scanning port {params.get('port', 80)}...")
    return True, {"vulns_found": 0}

# The Registry
TASK_REGISTRY = {
    "log_cleanup": run_log_cleanup_simulation,
    "security_scan": run_security_scan
}