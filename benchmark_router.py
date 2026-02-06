
import time
import re
from core.routing.tool_first_router import create_default_router, ToolType

def benchmark_router(router, queries, iterations=1000):
    start_time = time.time()
    for _ in range(iterations):
        for query in queries:
            router.route(query)
    end_time = time.time()
    return end_time - start_time

from core.routing.system_router import SystemRouter

def benchmark_system_router(router, queries, iterations=1000):
    start_time = time.time()
    for _ in range(iterations):
        for query in queries:
            router.route_and_execute(query)
    end_time = time.time()
    return end_time - start_time

if __name__ == "__main__":
    router = create_default_router()
    system_router = SystemRouter()
    test_queries = [
        "What is 15% of 250?",
        "What day is today?",
        "Analyze this regulatory requirement for compliance",
        "Summarize this long document",
        "Interpret this dashboard screenshot",
        "Debug the UI rendering issues in the empathy panel",
        "Parse the latest error logs from the truth-engine",
        "Extract all LEI numbers from the transaction report"
    ]
    
    duration = benchmark_router(router, test_queries)
    print(f"Original Router Duration: {duration:.4f}s")
    
    sys_duration = benchmark_system_router(system_router, test_queries)
    print(f"System Router Duration: {sys_duration:.4f}s")
