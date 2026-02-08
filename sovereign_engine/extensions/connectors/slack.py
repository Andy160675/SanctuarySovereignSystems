"""
Slack Connector - Real-time notifications.
Part of Connector Pack.
"""

import json
import requests
from typing import Dict, Optional

class SlackConnector:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or self._get_webhook_from_env()
    
    def _get_webhook_from_env(self):
        import os
        return os.getenv('SLACK_WEBHOOK_URL')
    
    def send_alert(self, message: str, severity: str = 'info', 
                   context: Optional[Dict] = None):
        """Send alert to Slack."""
        if not self.webhook_url:
            print("No Slack webhook configured")
            return False
        
        colors = {
            'info': '#36a64f',
            'warning': '#ffcc00',
            'error': '#ff0000',
            'critical': '#8b0000'
        }
        
        payload = {
            "attachments": [{
                "color": colors.get(severity, '#36a64f'),
                "title": f"Sovereign Engine Alert: {severity.upper()}",
                "text": message,
                "fields": [
                    {
                        "title": "Timestamp",
                        "value": self._get_timestamp(),
                        "short": True
                    }
                ]
            }]
        }
        
        if context:
            for key, value in context.items():
                payload['attachments'][0]['fields'].append({
                    "title": key,
                    "value": str(value),
                    "short": True
                })
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

# Observatory integration
def observatory_to_slack(observatory, slack_connector):
    """Send Observatory health reports to Slack."""
    report = observatory.generate_health_report()
    
    if report['status'] == 'warning':
        message = f"System drift detected: {report['drift']}"
        slack_connector.send_alert(
            message=message,
            severity='warning',
            context=report['metrics']
        )
    elif report['status'] == 'healthy':
        # Send periodic health check (once per day)
        import time
        if int(time.time()) % 86400 < 60:  # Once per day
            slack_connector.send_alert(
                message="Daily health check: System is healthy",
                severity='info',
                context={'checks_passed': 'All'}
            )
