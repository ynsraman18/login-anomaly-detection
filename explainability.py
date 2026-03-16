import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class ModelExplainer:
    """SHAP-based model explainability for anomaly detection"""
    
    def __init__(self, model, X_train: np.ndarray, feature_names: List[str]):
        """Initialize explainer with trained model and training data"""
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        self.explainer = None
        self.shap_values = None
        self._init_explainer()
    
    def _init_explainer(self):
        """Initialize SHAP TreeExplainer (fast for tree-based models)"""
        try:
            # For Isolation Forest, use TreeExplainer
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            print(f"Warning: Could not initialize TreeExplainer: {e}")
            print("Using KernelExplainer instead (slower)")
            # Fallback to KernelExplainer
            self.explainer = shap.KernelExplainer(
                self.model.predict,
                shap.sample(self.X_train, min(100, len(self.X_train)))
            )
    
    def explain_prediction(self, X_sample: np.ndarray) -> Dict:
        """
        Explain a single prediction using SHAP values
        Returns feature importance and contribution to anomaly score
        """
        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X_sample)
        
        # Handle both single and multiple outputs
        if isinstance(shap_values, list):
            # For binary classification, take anomaly class
            shap_vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            shap_vals = shap_values[0]
        
        # Get base value
        base_value = self.explainer.expected_value
        if isinstance(base_value, list):
            base_value = base_value[1] if len(base_value) > 1 else base_value[0]
        
        # Create feature importance breakdown
        feature_importance = []
        for idx, feature_name in enumerate(self.feature_names):
            feature_importance.append({
                'feature': feature_name,
                'value': float(X_sample[0][idx]),
                'shap_value': float(shap_vals[idx]),
                'contribution': 'increases_anomaly' if shap_vals[idx] > 0 else 'decreases_anomaly'
            })
        
        # Sort by absolute SHAP value
        feature_importance.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        
        return {
            'base_value': float(base_value),
            'total_prediction': float(base_value + np.sum(shap_vals)),
            'feature_importance': feature_importance,
            'top_features': feature_importance[:3],
            'anomaly_reason': self._generate_explanation(feature_importance[:3], X_sample[0])
        }
    
    def _generate_explanation(self, top_features: List[Dict], sample: np.ndarray) -> str:
        """Generate human-readable explanation of anomaly"""
        if not top_features:
            return "Unknown anomaly pattern"
        
        reasons = []
        for feat in top_features[:3]:
            feature = feat['feature']
            value = feat['value']
            contribution = feat['contribution']
            
            if contribution == 'increases_anomaly':
                if feature == 'failed_attempts' and value > 15:
                    reasons.append(f"High failed attempts ({int(value)})")
                elif feature == 'login_hour' and value < 6:
                    reasons.append(f"Unusual login time (hour {int(value)})")
                elif feature == 'login_frequency' and value > 100:
                    reasons.append(f"Excessive login frequency ({int(value)})")
                elif feature in ['latitude', 'longitude']:
                    reasons.append(f"Suspicious geographic location ({feature})")
                else:
                    reasons.append(f"Anomalous {feature}: {value:.2f}")
        
        if not reasons:
            reasons = ["Multiple factors detected"]
        
        return " + ".join(reasons[:2])
    
    def get_feature_importance_scores(self, X: np.ndarray) -> Dict[str, float]:
        """Get average feature importance across dataset"""
        shap_values = self.explainer.shap_values(X)
        
        if isinstance(shap_values, list):
            shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_vals = shap_values
        
        # Calculate mean absolute SHAP value per feature
        importance = {}
        for idx, feature_name in enumerate(self.feature_names):
            importance[feature_name] = float(np.mean(np.abs(shap_vals[:, idx])))
        
        return importance
    
    def explain_batch(self, X_batch: np.ndarray) -> List[Dict]:
        """Explain multiple predictions"""
        explanations = []
        for i in range(len(X_batch)):
            explanations.append(self.explain_prediction(X_batch[i:i+1]))
        return explanations


def analyze_anomaly_patterns(explanations: List[Dict]) -> Dict:
    """Analyze patterns across multiple anomalies"""
    if not explanations:
        return {}
    
    pattern_counts = {}
    for exp in explanations:
        for feat in exp['top_features']:
            feature = feat['feature']
            if feature not in pattern_counts:
                pattern_counts[feature] = 0
            pattern_counts[feature] += 1
    
    # Sort by frequency
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'most_common_anomaly_patterns': sorted_patterns,
        'pattern_percentages': {
            feat: round(100 * count / len(explanations), 2)
            for feat, count in sorted_patterns
        },
        'total_anomalies_analyzed': len(explanations)
    }


def get_feature_correlation_to_anomaly(X: np.ndarray, predictions: np.ndarray, 
                                       feature_names: List[str]) -> Dict[str, float]:
    """Analyze which features correlate most with anomalies"""
    X_df = pd.DataFrame(X, columns=feature_names)
    X_df['is_anomaly'] = (predictions == -1).astype(int)
    
    correlations = {}
    for feature in feature_names:
        corr = X_df[feature].corr(X_df['is_anomaly'])
        correlations[feature] = float(corr) if not np.isnan(corr) else 0.0
    
    return correlations
