import time
import random
import os
import concurrent.futures
from emit import TelemetryEmitter

def simulate_coordination_storm(nas_path, head_name, concurrency=50, total_requests=500):
    emitter = TelemetryEmitter(nas_path, head_name)
    print(f"Starting Coordination Storm Test: {concurrency} concurrency for {total_requests} requests on {head_name}")
    
    def request_consensus(request_id):
        start = time.time()
        # Simulate network/consensus delay
        time.sleep(random.uniform(0.1, 0.5))
        latency = (time.time() - start) * 1000
        
        emitter.emit(
            component="consensus_engine",
            op="request_quorum",
            latency_ms=latency,
            queue_depth=concurrency,
            result="success",
            payload={"request_id": request_id, "nodes_involved": 5}
        )
        return latency

    latencies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(request_consensus, i) for i in range(total_requests)]
        for future in concurrent.futures.as_completed(futures):
            latencies.append(future.result())
            
    avg_latency = sum(latencies) / len(latencies)
    print(f"Storm complete. Avg Latency: {avg_latency:.2f}ms. Max Latency: {max(latencies):.2f}ms")

if __name__ == "__main__":
    NAS_PATH = os.path.join(os.getcwd(), "NAS")
    simulate_coordination_storm(NAS_PATH, "PC4_MIND", concurrency=20, total_requests=100)
