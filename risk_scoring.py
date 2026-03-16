import numpy as np
from typing import Dict, Tuple

class RiskScorer:
    """Advanced multi-dimensional risk assessment"""
    
    def __init__(self):
        """Initialize risk thresholds and weights"""
        self.weights = {
            'failed_attempts': 0.35,
            'login_frequency': 0.25,
            'login_hour': 0.20,
            'geographic': 0.15,
            'device': 0.05
        }
        
        # Threat regions for geographic risk
        self.threat_regions = [
            {'name': 'Eastern Europe', 'lat': (45.0, 55.0), 'lon': (15.0, 45.0)},
            {'name': 'Middle East', 'lat': (15.0, 40.0), 'lon': (25.0, 60.0)},
            {'name': 'East Asia', 'lat': (30.0, 50.0), 'lon': (100.0, 150.0)},
            {'name': 'South Asia', 'lat': (10.0, 35.0), 'lon': (50.0, 85.0)},
            {'name': 'Africa', 'lat': (-35.0, 35.0), 'lon': (-20.0, 60.0)},
            {'name': 'North Korea', 'lat': (37.0, 43.0), 'lon': (124.0, 130.0)},
            {'name': 'Iran', 'lat': (25.0, 37.0), 'lon': (44.0, 60.0)},
            {'name': 'Dark Web Proxy', 'lat': (40.0, 60.0), 'lon': (-10.0, 30.0)}
        ]
    
    def score_login(self, login_data: Dict, decision_score: float, 
                   prediction: int) -> Tuple[Dict, str, float]:
        """
        Calculate comprehensive risk score for a login attempt
        
        Returns:
            - risk_details: Detailed breakdown of risk factors
            - risk_level: Classification (CRITICAL, HIGH, MEDIUM, LOW, NORMAL)
            - overall_risk: Numerical risk score (0-100)
        """
        
        # Calculate component risk scores
        failed_attempts_risk = self._score_failed_attempts(login_data.get('failed_attempts', 0))
        frequency_risk = self._score_frequency(login_data.get('login_frequency', 0))
        hour_risk = self._score_login_hour(login_data.get('login_hour', 12))
        geographic_risk = self._score_geographic(
            login_data.get('latitude', 0),
            login_data.get('longitude', 0)
        )
        device_risk = self._score_device(login_data.get('device_type', 1))
        
        # Combine with ML prediction
        model_anomaly_score = abs(decision_score) * 100  # Convert to 0-100
        if prediction == -1:
            model_anomaly_score *= 1.5  # Boost if flagged as anomaly
        
        # Calculate weighted overall risk
        feature_risk = (
            self.weights['failed_attempts'] * failed_attempts_risk +
            self.weights['login_frequency'] * frequency_risk +
            self.weights['login_hour'] * hour_risk +
            self.weights['geographic'] * geographic_risk +
            self.weights['device'] * device_risk
        )
        
        # Overall score: blend feature risk with model anomaly score
        overall_risk = min(100, (feature_risk * 0.4 + model_anomaly_score * 0.6))
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            prediction, decision_score, feature_risk
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            overall_risk, prediction, confidence
        )
        
        # Attack pattern probability
        attack_patterns = self._identify_attack_patterns(login_data)
        
        risk_details = {
            'overall_risk_score': round(overall_risk, 2),
            'confidence': round(confidence, 2),
            'risk_level': risk_level,
            'model_prediction': 'ANOMALY' if prediction == -1 else 'NORMAL',
            'decision_score': round(decision_score, 4),
            'component_scores': {
                'failed_attempts': round(failed_attempts_risk, 2),
                'login_frequency': round(frequency_risk, 2),
                'login_hour': round(hour_risk, 2),
                'geographic': round(geographic_risk, 2),
                'device': round(device_risk, 2),
                'model_anomaly': round(model_anomaly_score, 2)
            },
            'attack_patterns': attack_patterns,
            'probability_score': round(sum(1 for p in attack_patterns if p['detected']) / 
                                      max(len(attack_patterns), 1), 2)
        }
        
        return risk_details, risk_level, overall_risk
    
    def _score_failed_attempts(self, failed_attempts: int) -> float:
        """Score based on failed login attempts (credential stuffing indicator)"""
        if failed_attempts < 3:
            return 10.0
        elif failed_attempts < 8:
            return 30.0
        elif failed_attempts < 15:
            return 60.0
        elif failed_attempts < 25:
            return 85.0
        else:
            return 100.0
    
    def _score_frequency(self, login_frequency: int) -> float:
        """Score based on login frequency (bot activity indicator)"""
        if login_frequency < 20:
            return 10.0
        elif login_frequency < 50:
            return 25.0
        elif login_frequency < 100:
            return 50.0
        elif login_frequency < 150:
            return 75.0
        else:
            return 100.0
    
    def _score_login_hour(self, login_hour: int) -> float:
        """Score based on login hour (timing anomaly)"""
        # Normal business hours: 8-22 (8 AM to 10 PM)
        if 8 <= login_hour <= 22:
            return 10.0
        # Early morning risky: 2-7 AM
        elif 2 <= login_hour < 8:
            return 85.0
        # Very early risky: 0-1 AM
        elif login_hour < 2:
            return 95.0
        # Late night risky: 23-24
        else:
            return 75.0
    
    def _score_geographic(self, latitude: float, longitude: float) -> float:
        """Score based on geographic location (threat region detection)"""
        # Check if in threat region
        for region in self.threat_regions:
            lat_min, lat_max = region['lat']
            lon_min, lon_max = region['lon']
            
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                return 80.0  # High risk from threat region
        
        # Normal geographic areas
        if -45 <= latitude <= 60 and -120 <= longitude <= 150:
            return 15.0
        
        # Unusual but not threat region
        return 40.0
    
    def _score_device(self, device_type: int) -> float:
        """Score based on device type"""
        # 0: mobile, 1: laptop, 2: tablet
        # Laptop from office is normal
        if device_type == 1:
            return 10.0
        # Mobile slightly suspicious (could be attacker)
        elif device_type == 0:
            return 30.0
        # Tablet least common
        else:
            return 50.0
    
    def _calculate_confidence(self, prediction: int, decision_score: float, 
                            feature_risk: float) -> float:
        """Calculate confidence in the risk assessment (0-100)"""
        # Model confidence
        model_confidence = min(100, abs(decision_score) * 200)  # Scale to 0-100
        
        # Feature consistency
        if feature_risk > 60:
            feature_confidence = 90.0
        elif feature_risk > 40:
            feature_confidence = 70.0
        else:
            feature_confidence = 50.0
        
        # Agreement between model and features
        if prediction == -1 and feature_risk > 40:
            agreement_bonus = 20
        elif prediction == 1 and feature_risk < 40:
            agreement_bonus = 20
        else:
            agreement_bonus = 0
        
        confidence = min(100, (model_confidence + feature_confidence) / 2 + agreement_bonus)
        return confidence
    
    def _determine_risk_level(self, risk_score: float, prediction: int, 
                            confidence: float) -> str:
        """Determine categorical risk level"""
        
        if prediction == -1:  # Model flagged as anomaly
            if risk_score >= 80:
                return "CRITICAL"
            elif risk_score >= 60:
                return "HIGH"
            else:
                return "MEDIUM"
        else:  # Normal prediction
            if risk_score >= 60:
                return "HIGH"
            elif risk_score >= 40:
                return "MEDIUM"
            elif risk_score >= 20:
                return "LOW"
            else:
                return "NORMAL"
    
    def _identify_attack_patterns(self, login_data: Dict) -> list:
        """Identify specific attack patterns"""
        patterns = []
        
        # Pattern 1: Credential stuffing
        if login_data.get('failed_attempts', 0) > 15:
            patterns.append({
                'name': 'Credential Stuffing',
                'detected': True,
                'confidence': 0.95,
                'description': 'High number of failed attempts'
            })
        
        # Pattern 2: Night attack
        if login_data.get('login_hour', 12) < 6:
            patterns.append({
                'name': 'Night Attack',
                'detected': True,
                'confidence': 0.80,
                'description': 'Login attempt during unusual hours'
            })
        
        # Pattern 3: Bot activity
        if login_data.get('login_frequency', 0) > 100:
            patterns.append({
                'name': 'Bot Activity',
                'detected': True,
                'confidence': 0.85,
                'description': 'Excessive rapid login attempts'
            })
        
        # Pattern 4: Geographic threat
        for region in self.threat_regions:
            lat_min, lat_max = region['lat']
            lon_min, lon_max = region['lon']
            lat, lon = login_data.get('latitude', 0), login_data.get('longitude', 0)
            
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                patterns.append({
                    'name': 'Threat Region Access',
                    'detected': True,
                    'confidence': 0.90,
                    'description': f'Login from {region["name"]}'
                })
                break
        
        # Pattern 5: Unusual device
        if login_data.get('device_type', 1) == 2:  # Tablet
            patterns.append({
                'name': 'Unusual Device',
                'detected': True,
                'confidence': 0.50,
                'description': 'Login from uncommon device type'
            })
        
        return patterns
