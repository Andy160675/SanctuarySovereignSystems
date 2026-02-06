import sys
import time
import requests

SERVICES = {
    "Planner": "http://localhost:8090/health",
    "Advocate": "http://localhost:8091/health",
    "Confessor": "http://localhost:8092/health",
    "Watcher": "http://localhost:8093/health",
    "Ledger": "http://localhost:8082/health",
    "Kill-Switch": "http://localhost:8000/health"
}

def poll_services(timeout=60, interval=2):
    start_time = time.time()
    pending = list(SERVICES.keys())
    
    print(f"Waiting for services to initialize (timeout: {timeout}s)...")
    
    while time.time() - start_time < timeout:
        for name in pending[:]:
            try:
                response = requests.get(SERVICES[name], timeout=2)
                if response.status_code == 200:
                    print(f"  [✓] {name} is online")
                    pending.remove(name)
            except Exception:
                pass
        
        if not pending:
            print(f"All services online in {int(time.time() - start_time)}s.")
            return True
            
        time.sleep(interval)
    
    print(f"Timeout reached. Offline services: {pending}")
    return False

if __name__ == "__main__":
    success = poll_services()
    sys.exit(0 if success else 1)
