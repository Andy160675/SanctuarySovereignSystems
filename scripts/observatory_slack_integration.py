#!/usr/bin/env python3
"""
Observatory + Slack integration.
Quick win bolt-on implementation.
"""

import time
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from sovereign_engine.extensions.observatory import Observatory
from sovereign_engine.extensions.connectors.slack import (
    SlackConnector, observatory_to_slack
)

def main():
    print("Starting Observatory + Slack monitoring...")
    
    # Initialize components
    observatory = Observatory()
    slack = SlackConnector()
    
    if not slack.webhook_url:
        print("Warning: No SLACK_WEBHOOK_URL environment variable set")
        print("Monitoring will run but alerts won't be sent to Slack")
    
    # Set baseline
    print("Setting baseline metrics...")
    baseline = observatory.collect_telemetry()
    observatory.metrics['baseline'] = baseline
    print(f"Baseline established: CPU={baseline.get('cpu_percent') or 0}%, Memory={baseline.get('memory_percent') or 0}%")
    
    # Monitoring loop
    print("\nStarting monitoring loop (Ctrl+C to stop)...")
    try:
        # For testing purposes if --test is passed
        if "--test" in sys.argv:
            report = observatory.generate_health_report()
            print(f"Test Report Status: {report['status']}")
            print("Test complete.")
            return

        while True:
            # Check health
            report = observatory.generate_health_report()
            
            if report['status'] == 'warning':
                print(f"⚠️  Drift detected: {report['drift']}")
                if slack.webhook_url:
                    observatory_to_slack(observatory, slack)
            else:
                print(f"✓ System healthy - CPU: {report['metrics'].get('cpu_percent') or 0}%")
            
            time.sleep(300)  # Check every 5 minutes
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == '__main__':
    main()
