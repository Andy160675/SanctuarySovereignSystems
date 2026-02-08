"""
Article VII: The Pathology Detection Hooks
============================================
Anomaly markers, edge-case triggers, and boundary flags are
embedded in the kernel. They do not act, but they observe and
signal when a state approaches a defined pathology.

This makes systemic blindness impossible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List
from tools.sovereign_stack.engine.signals.typed_signal import TypedSignal, SignalType, create_signal, AuthorityLevel
from tools.sovereign_stack.engine.feedback.feedback_log import FeedbackLog, LogEntry


@dataclass(frozen=True)
class PathologyAlert:
    """Immutable alert record when a pathology threshold is breached."""
    pathology_name: str
    severity: str  # "warning", "critical", "constitutional"
    metric_value: float
    threshold: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PathologyDetector:
    """
    Passive observer. Detects anomalies and signals them.
    Does NOT act â€” only observes and reports.
    """

    def __init__(self, feedback_log: FeedbackLog):
        self._feedback_log = feedback_log
        self._alerts: list[PathologyAlert] = []
        self._thresholds = {
            "routing_failure_rate": 0.15,       # >15% failures = warning
            "escalation_frequency": 5,          # >5 escalations/cycle = warning
            "unhandled_signal_rate": 0.10,      # >10% unhandled = critical
            "chain_integrity_failures": 0,      # Any = constitutional
            "jurisdiction_violations": 0,       # Any = critical
        }

    @property
    def alerts(self) -> tuple[PathologyAlert, ...]:
        return tuple(self._alerts)

    def check_routing_health(
        self, total_signals: int, failed_signals: int
    ) -> list[PathologyAlert]:
        """Monitor routing failure rates."""
        alerts = []
        if total_signals == 0:
            return alerts

        rate = failed_signals / total_signals
        if rate > self._thresholds["routing_failure_rate"]:
            alert = PathologyAlert(
                pathology_name="high_routing_failure_rate",
                severity="warning",
                metric_value=rate,
                threshold=self._thresholds["routing_failure_rate"],
            )
            alerts.append(alert)
            self._record_alert(alert)

        if rate > self._thresholds["unhandled_signal_rate"]:
            alert = PathologyAlert(
                pathology_name="critical_unhandled_signal_rate",
                severity="critical",
                metric_value=rate,
                threshold=self._thresholds["unhandled_signal_rate"],
            )
            alerts.append(alert)
            self._record_alert(alert)

        return alerts

    def check_escalation_health(self, escalation_count: int) -> list[PathologyAlert]:
        """Monitor escalation frequency."""
        alerts = []
        if escalation_count > self._thresholds["escalation_frequency"]:
            alert = PathologyAlert(
                pathology_name="excessive_escalation_frequency",
                severity="warning",
                metric_value=float(escalation_count),
                threshold=float(self._thresholds["escalation_frequency"]),
            )
            alerts.append(alert)
            self._record_alert(alert)
        return alerts

    def check_chain_integrity(self, integrity_valid: bool) -> list[PathologyAlert]:
        """Monitor hash chain integrity â€” constitutional level."""
        alerts = []
        if not integrity_valid:
            alert = PathologyAlert(
                pathology_name="chain_integrity_violation",
                severity="constitutional",
                metric_value=1.0,
                threshold=0.0,
            )
            alerts.append(alert)
            self._record_alert(alert)
        return alerts

    def check_jurisdiction_violations(self, violation_count: int) -> list[PathologyAlert]:
        """Monitor cross-domain contamination attempts."""
        alerts = []
        if violation_count > self._thresholds["jurisdiction_violations"]:
            alert = PathologyAlert(
                pathology_name="jurisdiction_boundary_violation",
                severity="critical",
                metric_value=float(violation_count),
                threshold=float(self._thresholds["jurisdiction_violations"]),
            )
            alerts.append(alert)
            self._record_alert(alert)
        return alerts

    def _record_alert(self, alert: PathologyAlert) -> None:
        """Log the alert â€” passive observation only."""
        self._alerts.append(alert)
        self._feedback_log.append(LogEntry(
            signal_type="PATHOLOGY_ALERT",
            route_target=alert.severity,
            handler="pathology_detector",
            outcome="ALERT_RAISED",
            reason=f"{alert.pathology_name}: {alert.metric_value} > {alert.threshold}",
            evidence_hash="pathology_observation",
        ))

