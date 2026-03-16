import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Generate synthetic login behaviour data - EXPANDED DATASET
num_samples = 1200
normal_samples = int(num_samples * 0.90)
anomaly_samples = num_samples - normal_samples  # ~120 anomalies (10%)

# NORMAL USER BEHAVIOR (90% of data)
# Define actual major cities for normal logins
normal_cities = [
    {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060},
    {'name': 'London', 'lat': 51.5074, 'lon': -0.1278},
    {'name': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
    {'name': 'Sydney', 'lat': -33.8688, 'lon': 151.2093},
    {'name': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
    {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
    {'name': 'Toronto', 'lat': 43.6510, 'lon': -79.3470},
    {'name': 'São Paulo', 'lat': -23.5505, 'lon': -46.6333},
    {'name': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
    {'name': 'Singapore', 'lat': 1.3521, 'lon': 103.8198}
]

normal_city_choices = np.random.choice(normal_cities, normal_samples)
normal_lats = [city['lat'] + np.random.normal(0, 0.5) for city in normal_city_choices]
normal_lons = [city['lon'] + np.random.normal(0, 0.5) for city in normal_city_choices]

normal_data = {
    'login_hour': np.random.randint(8, 22, normal_samples),  # Business hours 8am-10pm
    'failed_attempts': np.random.randint(0, 3, normal_samples),  # Usually 0-2 failed attempts
    'device_type': np.random.randint(0, 3, normal_samples),  # 0: mobile, 1: laptop, 2: tablet
    'location_code': np.random.randint(1, 100, normal_samples),
    'login_frequency': np.random.randint(1, 40, normal_samples),  # 1-40 logins
    'latitude': normal_lats,
    'longitude': normal_lons,
    'travel_speed_mph': np.where(np.random.rand(normal_samples) > 0.9, np.random.uniform(5, 500, normal_samples), 0)
}

df_normal = pd.DataFrame(normal_data)

# DIVERSE ANOMALY PATTERNS (10% of data)
anomaly_types = {
    'high_failures': int(anomaly_samples * 0.25),      # High failed attempts (credential stuffing)
    'unusual_hours': int(anomaly_samples * 0.20),      # Logins at odd hours (attacks at 2-5 AM)
    'high_frequency': int(anomaly_samples * 0.15),     # Excessive rapid logins (bot activity)
    'geographic': int(anomaly_samples * 0.15),         # Suspicious locations (threat regions)
    'impossible_travel': int(anomaly_samples * 0.15),  # Impossible travel speeds
    'mixed': anomaly_samples - sum([int(anomaly_samples * 0.25), int(anomaly_samples * 0.20), 
                                     int(anomaly_samples * 0.15), int(anomaly_samples * 0.15),
                                     int(anomaly_samples * 0.15)])
}

anomaly_data = []

# Type 1: High failed attempts (credential stuffing attacks) target normal cities
for _ in range(anomaly_types['high_failures']):
    target = np.random.choice(normal_cities)
    anomaly_data.append({
        'login_hour': np.random.randint(0, 24),
        'failed_attempts': np.random.randint(20, 50),
        'device_type': np.random.choice([0, 1]),
        'location_code': np.random.randint(1, 100),
        'login_frequency': np.random.randint(40, 100),
        'latitude': target['lat'] + np.random.normal(0, 0.2),
        'longitude': target['lon'] + np.random.normal(0, 0.2),
        'travel_speed_mph': np.random.choice([0, np.random.uniform(5, 500)])
    })

# Type 2: Unusual hours (late night/early morning attacks) target normal cities
for _ in range(anomaly_types['unusual_hours']):
    target = np.random.choice(normal_cities)
    anomaly_data.append({
        'login_hour': np.random.choice([0, 1, 2, 3, 4, 5]),
        'failed_attempts': np.random.randint(5, 20),
        'device_type': np.random.choice([0, 1]),
        'location_code': np.random.randint(1, 100),
        'login_frequency': np.random.randint(30, 80),
        'latitude': target['lat'] + np.random.normal(0, 0.2),
        'longitude': target['lon'] + np.random.normal(0, 0.2),
        'travel_speed_mph': np.random.choice([0, np.random.uniform(5, 500)])
    })

# Type 3: High frequency (bot activity) target normal cities
for _ in range(anomaly_types['high_frequency']):
    target = np.random.choice(normal_cities)
    anomaly_data.append({
        'login_hour': np.random.randint(0, 24),
        'failed_attempts': np.random.randint(3, 15),
        'device_type': np.random.choice([0, 1]),
        'location_code': np.random.randint(1, 100),
        'login_frequency': np.random.randint(100, 200),
        'latitude': target['lat'] + np.random.normal(0, 0.2),
        'longitude': target['lon'] + np.random.normal(0, 0.2),
        'travel_speed_mph': np.random.choice([0, np.random.uniform(5, 500)])
    })

# Type 4: Geographic anomalies (logins from threat hotspots)
threat_cities = [
    {'name': 'Pyongyang', 'lat': 39.0392, 'lon': 125.7625},
    {'name': 'Tehran', 'lat': 35.6892, 'lon': 51.3890},
    {'name': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},
    {'name': 'St. Petersburg', 'lat': 59.9310, 'lon': 30.3609},
    {'name': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
    {'name': 'Lagos', 'lat': 6.5244, 'lon': 3.3792},
    {'name': 'Caracas', 'lat': 10.4806, 'lon': -66.9036},
    {'name': 'Damascus', 'lat': 33.5138, 'lon': 36.2765}
]

for _ in range(anomaly_types['geographic']):
    region = np.random.choice(threat_cities)
    anomaly_data.append({
        'login_hour': np.random.choice([2, 3, 4, 5]),
        'failed_attempts': np.random.randint(10, 30),
        'device_type': np.random.choice([0, 1]),
        'location_code': np.random.randint(50, 100),
        'login_frequency': np.random.randint(50, 150),
        'latitude': region['lat'] + np.random.normal(0, 0.5),
        'longitude': region['lon'] + np.random.normal(0, 0.5),
        'travel_speed_mph': np.random.choice([0, np.random.uniform(5, 500)])
    })

# Type 5: Mixed anomalies (combination of multiple suspicious patterns)
for _ in range(anomaly_types['mixed']):
    region = np.random.choice(threat_cities)
    anomaly_data.append({
        'login_hour': np.random.choice([1, 2, 3, 4]),
        'failed_attempts': np.random.randint(15, 40),
        'device_type': np.random.choice([0, 1]),
        'location_code': np.random.randint(70, 100),
        'login_frequency': np.random.randint(80, 180),
        'latitude': region['lat'] + np.random.normal(0, 0.5),
        'longitude': region['lon'] + np.random.normal(0, 0.5),
        'travel_speed_mph': np.random.choice([0, np.random.uniform(5, 500)])
    })

# Type 6: Impossible travel (session hijacking) target random cities but extreme speeds
for _ in range(anomaly_types['impossible_travel']):
    target = np.random.choice(normal_cities)
    anomaly_data.append({
        'login_hour': np.random.randint(0, 24),
        'failed_attempts': np.random.randint(0, 3), # often 0 failed attempts in hijacked sessions
        'device_type': np.random.choice([0, 1, 2]),
        'location_code': np.random.randint(1, 100),
        'login_frequency': np.random.randint(1, 40),
        'latitude': target['lat'] + np.random.normal(0, 0.2),
        'longitude': target['lon'] + np.random.normal(0, 0.2),
        'travel_speed_mph': np.random.uniform(3000, 20000) # Speed impossible for physical travel
    })

df_anomaly = pd.DataFrame(anomaly_data)

# Combine normal and anomalies
df = pd.concat([df_normal, df_anomaly], ignore_index=True)

# Shuffle the dataset for better training
df = df.sample(frac=1, random_state=42).reset_index(drop=True)



# Save dataset
df.to_csv('login_data.csv', index=False)

# Print statistics
print("=" * 70)
print("[OK] Generated {} login records with diverse anomalies".format(len(df)))
print("=" * 70)
print("Dataset shape: {}".format(df.shape))
print("\nANOMALY DISTRIBUTION:")
print("  - High failed attempts (credential stuffing): {} samples".format(anomaly_types['high_failures']))
print("  - Unusual hours (night attacks): {} samples".format(anomaly_types['unusual_hours']))
print("  - High frequency (bot activity): {} samples".format(anomaly_types['high_frequency']))
print("  - Geographic (threat regions): {} samples".format(anomaly_types['geographic']))
print("  - Impossible Travel (hijacking): {} samples".format(anomaly_types['impossible_travel']))
print("  - Mixed patterns: {} samples".format(anomaly_types['mixed']))
print("  - Total anomalies: {} ({:.1f}%)".format(anomaly_samples, 100*anomaly_samples/num_samples))
print("  - Normal samples: {} ({:.1f}%)".format(normal_samples, 100*normal_samples/num_samples))
print("\nTHREAT REGIONS COVERED: {} regions".format(len(threat_cities)))
print("\nSample anomalies from data:")
print(df[df['travel_speed_mph'] > 1000].head(5)[['login_hour', 'failed_attempts', 'travel_speed_mph', 'latitude', 'longitude']])
print("=" * 70)
