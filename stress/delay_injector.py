import time
import random
import os
from emit import TelemetryEmitter

def simulate_delayed_consensus(nas_path, head_name, delay_sec=30, failure_rate=0.5, total=10):
    emitter = TelemetryEmitter(nas_path, head_name)
    print(f"Starting Delayed Consensus Test: {delay_sec}s delay (rate {failure_rate}) on {head_name}")
    
    for i in range(total):
        is_delayed = random.random() < failure_rate
        start = time.time()
        
        if is_delayed:
            print(f"[{i}] Injecting {delay_sec}s delay...")
            time.sleep(delay_sec)
            result = "timeout_recovered"
        else:
            time.sleep(random.uniform(0.1, 0.5))
            result = "success"
            
        latency = (time.time() - start) * 1000
        emitter.emit(
            component="governance_gateway",
            op="authorize_workflow",
            latency_ms=latency,
            result=result,
            payload={"delayed": is_delayed}
        )
        
    print("Delay test complete.")

if __name__ == "__main__":
    NAS_PATH = os.path.join(os.getcwd(), "NAS")
    simulate_delayed_consensus(NAS_PATH, "PC4_MIND", delay_sec=5, failure_rate=0.3, total=5)
