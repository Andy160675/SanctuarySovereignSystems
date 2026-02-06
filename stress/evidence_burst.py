import time
import random
import os
from emit import TelemetryEmitter

def simulate_evidence_burst(nas_path, head_name, rps=100, duration=60):
    emitter = TelemetryEmitter(nas_path, head_name)
    start_time = time.time()
    count = 0
    
    print(f"Starting Evidence Burst Test: {rps} RPS for {duration}s on {head_name}")
    
    while time.time() - start_time < duration:
        loop_start = time.time()
        
        # Simulate evidence generation
        gen_start = time.time()
        # Mocking complex work
        _ = [random.random() for _ in range(1000)]
        gen_latency = (time.time() - gen_start) * 1000
        
        # Emit telemetry
        emitter.emit(
            component="evidence_engine",
            op="generate_receipt",
            latency_ms=gen_latency,
            queue_depth=random.randint(0, 10),
            result="success",
            payload={"agent_id": f"agent_{random.randint(1, 1000000)}"}
        )
        
        count += 1
        
        # Throttling to maintain RPS
        elapsed = time.time() - loop_start
        sleep_time = (1.0 / rps) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
            
    print(f"Burst complete. Total receipts: {count}")

if __name__ == "__main__":
    NAS_PATH = os.path.join(os.getcwd(), "NAS")
    simulate_evidence_burst(NAS_PATH, "PC3_HEART", rps=100, duration=10)
