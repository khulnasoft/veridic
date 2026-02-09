"""
Alert Manager

Sends notifications for critical events, regressions, and anomalies
via email, Slack, webhooks, or other channels.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AlertChannel(Enum):
    """Available alert channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Alert:
    """Alert notification."""
    id: str
    title: str
    message: str
    severity: str  # critical, high, medium, low
    channel: AlertChannel
    metadata: Dict[str, Any]
    timestamp: str
    sent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["channel"] = self.channel.value
        return data


class AlertManager:
    """
    Manages alert notifications across multiple channels.
    
    Supports:
    - Email notifications
    - Slack webhooks
- Custom webhooks
    - Logging (for testing)
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.alerts: List[Alert] = []
        self.handlers: Dict[AlertChannel, Callable] = {
            AlertChannel.LOG: self._handle_log,
        }
        self.alert_counter = 0
    
    def register_handler(self, channel: AlertChannel, handler: Callable):
        """
        Register a custom handler for an alert channel.
        
        Args:
            channel: Alert channel type
            handler: Function to handle alerts
        """
        self.handlers[channel] = handler
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: str,
        channel: AlertChannel = AlertChannel.LOG,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """
        Send an alert notification.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Severity level
            channel: Channel to send alert through
            metadata: Additional metadata
            
        Returns:
            Created Alert object
        """
        self.alert_counter += 1
        
        alert = Alert(
            id=f"alert-{self.alert_counter}",
            title=title,
            message=message,
            severity=severity,
            channel=channel,
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat(),
        )
        
        # Send through appropriate handler
        handler = self.handlers.get(channel)
        if handler:
            try:
                handler(alert)
                alert.sent = True
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
                alert.sent = False
        else:
            logger.warning(f"No handler registered for channel: {channel}")
        
        self.alerts.append(alert)
        return alert
    
    def send_regression_alert(
        self,
        asset_id: str,
        drift_percentage: float,
        current_score: float,
        previous_score: float,
        channel: AlertChannel = AlertChannel.LOG,
    ) -> Alert:
        """
        Send alert for regression detection.
        
        Args:
            asset_id: Asset identifier
            drift_percentage: Percentage drift
            current_score: Current threat score
            previous_score: Previous threat score
            channel: Alert channel
            
        Returns:
            Created Alert object
        """
        severity = "critical" if abs(drift_percentage) > 30 else "high"
        
        title = f"Security Regression Detected: {asset_id}"
        message = (
            f"Threat score increased by {drift_percentage:.1f}%\n"
            f"Previous score: {previous_score:.2f}\n"
            f"Current score: {current_score:.2f}\n"
            f"Asset: {asset_id}"
        )
        
        metadata = {
            "asset_id": asset_id,
            "drift_percentage": drift_percentage,
            "current_score": current_score,
            "previous_score": previous_score,
        }
        
        return self.send_alert(title, message, severity, channel, metadata)
    
    def send_anomaly_alert(
        self,
        anomaly_type: str,
        description: str,
        asset_id: str,
        severity: str,
        channel: AlertChannel = AlertChannel.LOG,
    ) -> Alert:
        """
        Send alert for anomaly detection.
        
        Args:
            anomaly_type: Type of anomaly
            description: Description
            asset_id: Asset identifier
            severity: Severity level
            channel: Alert channel
            
        Returns:
            Created Alert object
        """
        title = f"Anomaly Detected: {anomaly_type}"
        message = f"{description}\nAsset: {asset_id}"
        
        metadata = {
            "anomaly_type": anomaly_type,
            "asset_id": asset_id,
        }
        
        return self.send_alert(title, message, severity, channel, metadata)
    
    def send_ci_failure_alert(
        self,
        reason: str,
        details: Dict[str, Any],
        channel: AlertChannel = AlertChannel.LOG,
    ) -> Alert:
        """
        Send alert for CI/CD failure.
        
        Args:
            reason: Failure reason
            details: Failure details
            channel: Alert channel
            
        Returns:
            Created Alert object
        """
        title = "CI/CD Check Failed"
        message = f"Reason: {reason}\n" + "\n".join(
            f"{k}: {v}" for k, v in details.items()
        )
        
        return self.send_alert(title, message, "high", channel, details)
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        sent: Optional[bool] = None,
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            severity: Filter by severity
            sent: Filter by sent status
            
        Returns:
            List of filtered alerts
        """
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if sent is not None:
            alerts = [a for a in alerts if a.sent == sent]
        
        return alerts
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()
        self.alert_counter = 0
    
    # Built-in handlers
    def _handle_log(self, alert: Alert):
        """Handle alert via logging."""
        log_level = {
            "critical": logging.CRITICAL,
            "high": logging.ERROR,
            "medium": logging.WARNING,
            "low": logging.INFO,
        }.get(alert.severity, logging.INFO)
        
        logger.log(
            log_level,
            f"ALERT [{alert.severity.upper()}] {alert.title}: {alert.message}",
        )
    
    def _handle_email(self, alert: Alert):
        """Handle alert via email (stub - requires SMTP configuration)."""
        # TODO: Implement email sending
        logger.info(f"Would send email alert: {alert.title}")
    
    def _handle_slack(self, alert: Alert):
        """Handle alert via Slack webhook (stub)."""
        # TODO: Implement Slack webhook
        logger.info(f"Would send Slack alert: {alert.title}")
    
    def _handle_webhook(self, alert: Alert):
        """Handle alert via custom webhook (stub)."""
        # TODO: Implement webhook POST
        logger.info(f"Would send webhook alert: {alert.title}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = AlertManager()
    
    # Send regression alert
    alert1 = manager.send_regression_alert(
        asset_id="asset-123",
        drift_percentage=35.5,
        current_score=85.3,
        previous_score=62.9,
    )
    
    print(f"Alert sent: {alert1.id}")
    print(f"  Title: {alert1.title}")
    print(f"  Severity: {alert1.severity}")
    print(f"  Sent: {alert1.sent}")
    
    # Send anomaly alert
    alert2 = manager.send_anomaly_alert(
        anomaly_type="score_spike",
        description="Score increased by 5 standard deviations",
        asset_id="asset-456",
        severity="critical",
    )
    
    print(f"\nAlert sent: {alert2.id}")
    
    # Get all critical alerts
    critical_alerts = manager.get_alerts(severity="critical")
    print(f"\nTotal critical alerts: {len(critical_alerts)}")
