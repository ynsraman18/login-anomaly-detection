import os
from typing import Dict, Optional
from datetime import datetime
import json

class AlertManager:
    """Real-time alerting system with Slack integration"""
    
    def __init__(self, slack_webhook_url: Optional[str] = None):
        """Initialize alert manager"""
        self.slack_webhook_url = slack_webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.alert_history = {}  # Track sent alerts to prevent duplicates
        self.alert_throttle = {}  # Throttle alerts by IP
        self.max_alerts_per_ip_per_hour = 5
    
    def create_alert(self, prediction_id: int, risk_details: Dict, 
                    login_data: Dict) -> Dict:
        """Create an alert from risk assessment"""
        
        severity = risk_details['risk_level']
        risk_score = risk_details['overall_risk_score']
        confidence = risk_details['confidence']
        
        # Determine alert type based on severity
        if severity == "CRITICAL":
            alert_type = "CRITICAL_THREAT"
            description = "CRITICAL anomaly detected - potential active attack"
            should_alert = True
        elif severity == "HIGH":
            alert_type = "HIGH_RISK"
            description = "High-risk login anomaly detected"
            should_alert = True
        elif severity == "MEDIUM":
            alert_type = "MEDIUM_RISK"
            description = "Medium-risk login anomaly detected"
            should_alert = confidence > 0.75  # Only alert if confident
        else:
            alert_type = "LOW_RISK"
            description = "Low-risk anomaly detected"
            should_alert = False
        
        alert = {
            'prediction_id': prediction_id,
            'severity': severity,
            'alert_type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'title': f"{severity} - {alert_type}",
            'description': description,
            'risk_score': risk_score,
            'confidence': confidence,
            'login_data': login_data,
            'risk_details': risk_details,
            'should_alert': should_alert,
            'message': self._build_alert_message(risk_details, login_data)
        }
        
        return alert
    
    def _build_alert_message(self, risk_details: Dict, login_data: Dict) -> str:
        """Build human-readable alert message"""
        risk_level = risk_details['risk_level']
        risk_score = risk_details['overall_risk_score']
        confidence = risk_details['confidence']
        
        message = f"""
ALERT: {risk_level} RISK DETECTED
Risk Score: {risk_score}/100 | Confidence: {confidence}%

Location: ({login_data['latitude']:.2f}, {login_data['longitude']:.2f})
Time: Hour {login_data['login_hour']}
Failed Attempts: {login_data['failed_attempts']}
Login Frequency: {login_data['login_frequency']}

Attack Patterns Detected:
{self._format_attack_patterns(risk_details['attack_patterns'])}

Component Risk Breakdown:
- Failed Attempts: {risk_details['component_scores']['failed_attempts']}/100
- Login Frequency: {risk_details['component_scores']['login_frequency']}/100
- Login Hour: {risk_details['component_scores']['login_hour']}/100
- Geographic: {risk_details['component_scores']['geographic']}/100
- Device: {risk_details['component_scores']['device']}/100
"""
        return message.strip()
    
    def _format_attack_patterns(self, patterns: list) -> str:
        """Format attack patterns for display"""
        detected = [p['name'] for p in patterns if p['detected']]
        if detected:
            return "\n".join([f"  • {p}" for p in detected])
        return "  • None detected"
    
    def send_slack_alert(self, alert: Dict) -> bool:
        """Send alert to Slack"""
        if not self.slack_webhook_url or not alert['should_alert']:
            return False
        
        try:
            import requests
            
            # Determine color based on severity
            color_map = {
                'CRITICAL': '#FF0000',  # Red
                'HIGH': '#FF6600',      # Orange
                'MEDIUM': '#FFD700',    # Gold
                'LOW': '#00AA00'        # Green
            }
            
            color = color_map.get(alert['severity'], '#808080')
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert['title'],
                        "text": alert['message'],
                        "fields": [
                            {
                                "title": "Risk Score",
                                "value": f"{alert['risk_score']}/100",
                                "short": True
                            },
                            {
                                "title": "Confidence",
                                "value": f"{alert['confidence']}%",
                                "short": True
                            },
                            {
                                "title": "Location",
                                "value": f"({alert['login_data']['latitude']:.2f}, {alert['login_data']['longitude']:.2f})",
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": f"Hour {alert['login_data']['login_hour']}",
                                "short": True
                            },
                            {
                                "title": "Failed Attempts",
                                "value": str(alert['login_data']['failed_attempts']),
                                "short": True
                            },
                            {
                                "title": "Login Frequency",
                                "value": str(alert['login_data']['login_frequency']),
                                "short": True
                            }
                        ],
                        "footer": "AI Login Anomaly Detection",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=5
            )
            
            return response.status_code == 200
        
        except ImportError:
            print("Warning: requests library not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error sending Slack alert: {e}")
            return False
    
    def send_email_alert(self, alert: Dict, recipient: str) -> bool:
        """Send alert via email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            sender_email = os.getenv('SENDER_EMAIL')
            sender_password = os.getenv('SENDER_PASSWORD')
            
            if not all([sender_email, sender_password]):
                print("Email credentials not configured")
                return False
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = alert['title']
            message["From"] = sender_email
            message["To"] = recipient
            
            # Create HTML content
            html = f"""
            <html>
              <body>
                <h2 style="color: red;">{alert['title']}</h2>
                <pre>{alert['message']}</pre>
                <p><small>Sent at: {alert['timestamp']}</small></p>
              </body>
            </html>
            """
            
            part = MIMEText(html, "html")
            message.attach(part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient, message.as_string())
            
            return True
        
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False
    
    def should_throttle_alert(self, ip_address: str) -> bool:
        """Check if alert should be throttled for this IP"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        key = f"{ip_address}:{current_hour}"
        
        if key not in self.alert_throttle:
            self.alert_throttle[key] = 0
        
        self.alert_throttle[key] += 1
        
        return self.alert_throttle[key] > self.max_alerts_per_ip_per_hour
    
    def log_alert(self, alert: Dict) -> None:
        """Log alert to file"""
        try:
            with open('alerts.log', 'a') as f:
                f.write(json.dumps(alert, default=str) + '\n')
        except Exception as e:
            print(f"Error logging alert: {e}")


class AlertPolicy:
    """Alert escalation and routing policies"""
    
    @staticmethod
    def get_recipients(severity: str) -> Dict[str, list]:
        """Get alert recipients based on severity"""
        recipients = {
            'CRITICAL': {
                'slack_channel': '#critical-threats',
                'email': [os.getenv('SECURITY_LEAD_EMAIL', 'security@company.com')],
                'page_on_call': True,
                'escalate_to_soc': True
            },
            'HIGH': {
                'slack_channel': '#security-alerts',
                'email': [os.getenv('SOC_ANALYST_EMAIL', 'soc@company.com')],
                'page_on_call': False,
                'escalate_to_soc': False
            },
            'MEDIUM': {
                'slack_channel': '#security-alerts',
                'email': [],
                'page_on_call': False,
                'escalate_to_soc': False
            },
            'LOW': {
                'slack_channel': '#anomalies',
                'email': [],
                'page_on_call': False,
                'escalate_to_soc': False
            }
        }
        
        return recipients.get(severity, recipients['LOW'])
    
    @staticmethod
    def should_create_incident(severity: str) -> bool:
        """Determine if incident should be created in ticketing system"""
        return severity in ['CRITICAL', 'HIGH']
