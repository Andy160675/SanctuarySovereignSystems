"""
Observatory - Live telemetry, health, and drift monitoring.
S3-EXT-006: Foundation monitoring bolt-on.
"""

class Observatory:
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def collect_telemetry(self):
        """Collect system telemetry."""
        import time
        import psutil
        import sys
        
        self.metrics = {
            'timestamp': time.time(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('.').percent,
            'python_version': sys.version,
            'kernel_tests_passed': self._run_kernel_check()
        }
        return self.metrics
    
    def _run_kernel_check(self):
        """Run kernel invariant tests."""
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, '-m', 'sovereign_engine.tests.run_all'],
            capture_output=True, text=True
        )
        return '74/74 passed' in result.stdout
    
    def check_drift(self, baseline_metrics):
        """Check for system drift from baseline."""
        current = self.collect_telemetry()
        drift = {}
        
        for key in baseline_metrics:
            if key in current and key != 'timestamp':
                try:
                    change = abs(current[key] - baseline_metrics[key])
                    if change > 10:  # 10% threshold
                        drift[key] = f'{change:.1f}% change from baseline'
                except (TypeError, ValueError):
                    continue
        
        return drift
    
    def generate_health_report(self):
        """Generate health report."""
        metrics = self.collect_telemetry()
        # If no baseline is set in internal metrics, we use current metrics as baseline for check_drift
        baseline = self.metrics.get('baseline', metrics)
        drift = self.check_drift(baseline)
        
        return {
            'status': 'healthy' if not drift else 'warning',
            'metrics': metrics,
            'drift': drift,
            'timestamp': metrics['timestamp']
        }
    
    def get_baseline(self):
        """Return the baseline metrics."""
        return self.metrics.get('baseline', {})
