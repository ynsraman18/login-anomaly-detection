import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from auth import AuthDatabase, RoleChecker
from explainability import ModelExplainer

st.markdown("""
<style>

/* Page background */
.stApp {
    background: rgba(255,255,255);
}

/* Login container */
.login-box{
    background: rgba(20,20,20,0.9);
    padding: 40px;
    border-radius: 12px;
    border: 1px solid #30363d;
    box-shadow: 0px 0px 20px rgba(0,0,0,0.5);
}

/* Input fields */
input{
    background:#161b22 !important;
    color:white !important;
    border-radius:8px !important;
}

/* Login button */
button[kind="primary"]{
    background:#238636 !important;
    border-radius:8px !important;
}

/* Button hover */
button[kind="primary"]:hover{
    background:#2ea043 !important;
}

/* Tabs */
button[role="tab"]{
    font-weight:600;
}

/* Footer text */
.footer-text{
    text-align:center;
    color:#8b949e;
    font-size:0.8rem;
}

</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'token' not in st.session_state:
    st.session_state.token = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# Initialize authentication
auth_db = AuthDatabase()

# ============ AUTHENTICATION PAGE ============
def login_page():
    """Display login form"""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>Enterprise Secure</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #8b949e; font-weight: 400;'>AI Anomaly Detection Portal</h4>", unsafe_allow_html=True)
        
        st.divider()
        
        tab1, tab2 = st.tabs(["Login", "Organization Registration"])
        
        with tab1:
            username = st.text_input("Official Email ID", placeholder="Enter your organization email (e.g., admin@company.com)")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            if st.button("Login", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, result = auth_db.authenticate(username, password)
                    if success:
                        st.session_state.token = result
                        st.session_state.logged_in = True
                        # Decode token to get user info
                        import jwt
                        payload = jwt.decode(result, auth_db.secret_key, algorithms=['HS256'])
                        st.session_state.user = {
                            'username': payload['username'],
                            'role': payload['role'],
                            'user_id': payload['user_id']
                        }
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result}")
        
        with tab2:
            st.info("""
            **Organization Registration:**
            Enterprise Secure AI requires users to log in securely using their official organization email ID to ensure compliance.
            
            *(For demo presentation purposes, a default account exists: `admin` / `admin123`)*
            """)
            
            if st.button("Register Organization", type="secondary", use_container_width=True):
                st.session_state.show_create_user = True
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()
        st.markdown("<p style='text-align: center; color:#8b949e; font-size: 0.8rem;'><i>Zero-Trust Architecture powered by JWT</i></p>", unsafe_allow_html=True)


def create_user_form():
    """Form to create new user"""
    st.markdown("### Create New User")
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Official Email ID")
        email = st.text_input("Organization Name (Optional)")
    
    with col2:
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["viewer", "analyst", "admin"])
    
    if st.button("Create User", type="primary"):
        if not all([username, email, password]):
            st.error("All fields required")
        else:
            success, message = auth_db.create_user(username, email, password, role)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    if st.button("Back to Login"):
        st.session_state.show_create_user = False
        st.rerun()


def check_authentication():
    """Check if user is authenticated"""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        if 'show_create_user' in st.session_state and st.session_state.show_create_user:
            create_user_form()
        else:
            login_page()
        st.stop()


# Check authentication
check_authentication()

# Set page config
st.set_page_config(page_title="Login Anomaly Detection", layout="wide")

# Load model and data
@st.cache_resource
def load_model():
    return joblib.load('model.pkl')

@st.cache_data
def load_data():
    return pd.read_csv('login_data.csv')

model = load_model()
df = load_data()

# Add anomaly predictions
df['anomaly'] = model.predict(df[['login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']])
df['risk_score'] = abs(model.decision_function(df[['login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']]))
df['anomaly_label'] = df['anomaly'].apply(lambda x: 'Anomaly' if x == -1 else 'Normal')

# Initialize Explainer
feature_cols = ['login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']
explainer = ModelExplainer(model, df[feature_cols].values, feature_cols)

# ============ CUSTOM CSS ============
st.markdown("""
<style>
    /* Main Dashboard Background & Font styling */
    .stApp {
        background-color: #050505;
        color: #e6edf3;
        font-family: "Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    h1 { font-size: 2.8rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 2.0rem !important; }
    h3 {
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1f1f1f;
        margin-bottom: 1.5rem !important;
    }
    p, span, div {
        color: #a1a1aa; /* Soft gray for high-end readability */
    }
    strong, b { color: #ffffff !important; }

    /* Refined metric cards with sleek b&w mapping */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.05em;
    }
    [data-testid="stMetricLabel"] p {
        font-size: 1.1rem;
        color: #a1a1aa !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetric"] {
        background: #0a0a0a;
        border: 1px solid #27272a;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-6px);
        border-color: #ffffff;
        box-shadow: 0 12px 24px rgba(255, 255, 255, 0.08);
        background: #111111;
    }
    
    /* Streamlined Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        font-size: 0.85rem;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        border: 1px solid #ffffff !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .stButton>button *, .stButton>button div, .stButton>button p, .stButton>button span {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    .stButton>button:hover {
        border-color: #e4e4e7 !important;
        background-color: #e4e4e7 !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(255,255,255,0.2);
        transform: translateY(-2px);
    }
    .stButton>button[kind="primary"] {
        background-color: #f4f4f5 !important;
        color: #000000 !important;
        border: 1px solid #f4f4f5 !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #e4e4e7 !important;
        color: #000000 !important;
        border-color: #e4e4e7 !important;
        box-shadow: 0 0 20px rgba(255,255,255,0.3);
    }
    .stButton>button:active {
        transform: translateY(0px) !important;
    }
    
    /* Input Fields (Text, Select, File) */
    .stTextInput input, .stPasswordInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0a0a0a !important;
        border: 1px solid #27272a !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.5rem 1rem !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stTextInput input:focus, .stPasswordInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: #ffffff !important;
        box-shadow: 0 0 0 1px #ffffff !important;
    }
    
    /* File Uploader styling */
    [data-testid="stFileUploader"] {
        border: 1px dashed #3f3f46;
        border-radius: 12px;
        background-color: #0a0a0a;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #ffffff;
        background-color: #111111;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 2px solid #27272a;
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a1a1aa;
        font-weight: 500;
        font-size: 1.05rem;
        padding: 1rem 0;
        border-bottom: 2px solid transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #ffffff !important;
    }
    
    /* Expanders */
    [data-testid="stExpander"] {
        border: 1px solid #27272a;
        border-radius: 12px;
        background-color: #0a0a0a;
        overflow: hidden;
    }
    [data-testid="stExpander"] > summary {
        background-color: #111111;
        padding: 1rem 1.5rem;
        font-weight: 600;
        color: #ffffff;
    }
    [data-testid="stExpander"] > summary:hover {
        color: #ffffff;
        background-color: #18181b;
    }
    
    /* Alerts and feedback boxes */
    .stAlert {
        border-radius: 12px;
        border: 1px solid #27272a;
        color: #ffffff;
    }
    [data-testid="stAlert"] {
        background-color: #0a0a0a !important; 
    }
    
    /* Login Box specific styling */
    .element-container:has(.login-box) {
        background: #0a0a0a;
        border: 1px solid #27272a;
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.8);
    }
    
    /* Custom divider styling */
    hr {
        border-color: #1f1f22 !important;
        margin-top: 3rem !important;
        margin-bottom: 3rem !important;
    }
    
    /* Responsive dataframe */
    [data-testid="stDataFrame"] {
        width: 100%;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #27272a;
    }
    
    /* Download button specific adjustments to align nicely */
    [data-testid="stDownloadButton"] > button {
        width: 100%;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============ HEADER ============
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("<h1>Enterprise Secure AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; font-size: 1.1rem; border-left: 3px solid #ffffff; padding-left: 12px; margin-left: 2px;'>Organization Self-Service Threat Intelligence Portal</p>", unsafe_allow_html=True)

with col2:
    if st.session_state.user:
        user_info = st.session_state.user
        st.markdown(f"**Org:** {user_info['username']}")
        st.markdown(f"**Role:** {user_info['role']}")
        
        if st.button("Logout", type="secondary"):
            auth_db.logout(st.session_state.token)
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.token = None
            st.session_state.current_page = 'home'
            st.success("Logged out successfully")
            st.rerun()

st.divider()

# ============ DYNAMIC PAGE ROUTING ============
if st.session_state.current_page == 'home':
    st.markdown("<div style='text-align: center; margin-top: 50px; margin-bottom: 50px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 3.5rem;'>Zero-Trust Threat Detection</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.25rem; color: #8b949e; max-width: 800px; margin: 0 auto 30px auto;'>Welcome to your organization's self-service security portal. Protect your infrastructure against advanced threat actors, session hijacking, and geographic anomalies by analyzing your raw login telemetry through our Isolation Forest ML framework.</p>", unsafe_allow_html=True)
    
    colA, colB, colC = st.columns([1, 1, 1])
    with colB:
        if st.button("Detect Anomalies", type="primary", use_container_width=True):
            st.session_state.current_page = 'detect'
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_page == 'detect':
    if st.button("← Back to Organization Home", type="secondary"):
        st.session_state.current_page = 'home'
        st.rerun()
        
    st.divider()    
    st.markdown("<h2>Organization Log Verification</h2>", unsafe_allow_html=True)
    st.write("Upload a CSV export of your organization's recent SIEM login logs. The engine will evaluate the data and automatically highlight compromised sessions. Anomalies are grouped by primary User ID, alongside a 2-3 point AI reasoning description generated by SHAP Explainability.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    has_predict_permission = st.session_state.user and RoleChecker.can_access(st.session_state.user['role'], 'predict')

    colA, colB = st.columns([1, 1])
    with colA:
        sample_csv = "user_id,login_hour,failed_attempts,device_type,location_code,login_frequency,latitude,longitude,travel_speed_mph\nU-001,14,0,1,50,25,40.7128,-74.0060,0\nU-001,15,1,1,50,26,40.7128,-74.0060,5\nU-002,2,15,0,99,150,55.7558,37.6173,8500\nU-003,3,25,0,88,140,39.9042,116.4074,500\nU-004,10,0,2,20,5,51.5074,-0.1278,0\nU-004,10,0,2,20,6,-33.8688,151.2093,12000"
        st.download_button("Download Official CSV Template", sample_csv, "organization_log_template.csv", "text/csv")
    
    uploaded_file = st.file_uploader("Upload Telemetry CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.info(f"Successfully loaded {len(batch_df)} organization login records.")
            
            required_cols = ['user_id', 'login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']
            
            if not all(col in batch_df.columns for col in required_cols):
                 st.error(f"Missing required columns. Please ensure all these columns are present: {', '.join(required_cols)}")
            else:
                 if not has_predict_permission:
                     st.warning("You have 'Viewer' access. Running batch predictions requires 'Analyst' or 'Admin' privileges.")
                     st.button("Run Batch Analysis (Restricted)", disabled=True)
                 else:
                     if st.button("Run Batch Analysis", type="primary"):
                         # Run Inference
                         with st.spinner("Executing Zero-Trust Inference Engine..."):
                             X_batch = batch_df[['login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']]
                             batch_df['prediction'] = model.predict(X_batch)
                             batch_df['risk_score'] = abs(model.decision_function(X_batch))
                             
                             batch_anomalies = batch_df[batch_df['prediction'] == -1].copy()
                             
                             # Generate explanations for anomalies
                             reasons = []
                             for _, row in batch_anomalies.iterrows():
                                 sample = row[['login_hour', 'failed_attempts', 'device_type', 'location_code', 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']].values.reshape(1, -1)
                                 explanation = explainer.explain_prediction(sample)
                                 reasons.append(explanation['anomaly_reason'])
                             batch_anomalies['AI_Reasoning'] = reasons
                             
                         # Display Results
                         st.markdown("---")
                         if len(batch_anomalies) > 0:
                             st.error(f"**CRITICAL ALERTS:** Found {len(batch_anomalies)} anomalies out of {len(batch_df)} total logins processed.")
                             
                             st.markdown("##### Compromised Profiles Grouped by Primary User ID")
                             user_groups = batch_anomalies.groupby('user_id')
                             
                             for user_id, group in user_groups:
                                 with st.expander(f"User ID: {user_id} ({len(group)} anomalous events detected)"):
                                     display_cols = ['login_hour', 'failed_attempts', 'device_type', 'location_code', 'travel_speed_mph', 'risk_score', 'AI_Reasoning']
                                     
                                     formatted_group = group[display_cols].copy()
                                     formatted_group['risk_score'] = formatted_group['risk_score'].apply(lambda x: f"{x:.4f}")
                                     formatted_group.columns = ['Hour', 'Failed Attempts', 'Device', 'Location', 'Speed (MPH)', 'Risk Score', 'AI Reasoning (2-3 Points)']
                                     
                                     st.dataframe(formatted_group, use_container_width=True)
                             
                             # Add new visual graphs for anomalies
                             st.markdown("<br>", unsafe_allow_html=True)
                             st.markdown("##### Anomaly Intelligence Distributions")
                             col_g1, col_g2 = st.columns(2)
                             
                             with col_g1:
                                 st.markdown("**Anomalies by Hour of Day**")
                                 fig1, ax1 = plt.subplots(figsize=(6, 4))
                                 fig1.patch.set_alpha(0.0)
                                 ax1.set_facecolor('#050505')
                                 hour_counts = batch_anomalies['login_hour'].value_counts().sort_index()
                                 if not hour_counts.empty:
                                     ax1.bar(hour_counts.index.astype(str), hour_counts.values, color='#cccccc', edgecolor='#050505')
                                 ax1.set_xlabel('Hour (24h format)', color='#8b949e')
                                 ax1.set_ylabel('Incident Volume', color='#8b949e')
                                 ax1.tick_params(colors='#8b949e')
                                 for spine in ax1.spines.values():
                                     spine.set_color('#2a2a2a')
                                 ax1.grid(axis='y', alpha=0.15, color='#8b949e')
                                 fig1.tight_layout()
                                 st.pyplot(fig1)

                             with col_g2:
                                 st.markdown("**Anomalies by Device Type**")
                                 fig2, ax2 = plt.subplots(figsize=(6, 4))
                                 fig2.patch.set_alpha(0.0)
                                 ax2.set_facecolor('#050505')
                                 device_mapping = {0: 'Mobile', 1: 'Laptop', 2: 'Tablet'}
                                 dev_names = batch_anomalies['device_type'].map(device_mapping)
                                 dev_counts = dev_names.value_counts()
                                 if not dev_counts.empty:
                                     ax2.bar(dev_counts.index, dev_counts.values, color='#ffffff', edgecolor='#050505')
                                 ax2.set_ylabel('Incident Volume', color='#8b949e')
                                 ax2.tick_params(colors='#8b949e')
                                 for spine in ax2.spines.values():
                                     spine.set_color('#2a2a2a')
                                 ax2.grid(axis='y', alpha=0.15, color='#8b949e')
                                 fig2.tight_layout()
                                 st.pyplot(fig2)
                                 
                         else:
                             st.success(f"Processed {len(batch_df)} logins. No anomalies detected natively within this organization block.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

st.divider()

# ============ FOOTER ============
st.markdown("---")
st.markdown("<p style='text-align: center; color: #8b949e;'><b>Zero-Trust Access Portal</b> | Isolation Forest ML Subsystem | Build 2026.04</p>", unsafe_allow_html=True)
