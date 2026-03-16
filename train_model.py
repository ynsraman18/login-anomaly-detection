import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
from database import Database
from risk_scoring import RiskScorer

# Initialize database
db = Database()
risk_scorer = RiskScorer()

# Load the dataset
df = pd.read_csv('login_data.csv')

print("[INFO] Training Isolation Forest model...")
print("Dataset shape: {}".format(df.shape))

# Extract numeric features (including GPS and speed)
X = df[['login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']]

# Train Isolation Forest with contamination = 0.1
model = IsolationForest(contamination=0.1, random_state=42)
predictions = model.fit_predict(X)
decision_scores = model.decision_function(X)

# Add predictions to dataframe
df['anomaly'] = predictions
df['anomaly_label'] = df['anomaly'].apply(lambda x: 'Anomaly' if x == -1 else 'Normal')
df['decision_score'] = decision_scores

# Save the model
joblib.dump(model, 'model.pkl')
print("[OK] Model trained and saved to model.pkl")

# Store training data in database for audit and analytics
db.add_audit_log(
    'model_training',
    'Trained IsolationForest with contamination=0.1 on {} records'.format(len(df)),
    'system'
)

# Display statistics
normal_count = (df['anomaly'] == 1).sum()
anomaly_count = (df['anomaly'] == -1).sum()

print("\n[STATS] Training Statistics:")
print("   Normal logins: {}".format(normal_count))
print("   Anomalous logins: {}".format(anomaly_count))
print("   Anomaly percentage: {:.2f}%".format(anomaly_count / len(df) * 100))

print("\n[SAMPLES] Sample anomalies detected:")
print(df[df['anomaly'] == -1].head(10))
