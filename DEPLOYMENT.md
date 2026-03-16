# Production Deployment Guide

## 🚀 Ready to Deploy

Your AI Login Anomaly Detection system is production-ready. Follow this guide for enterprise deployment.

---

## Phase 1: Pre-Deployment (Day 1)

### 1. Security Hardening

#### Change Admin Password
```python
# In Python shell:
from auth import AuthDatabase
db = AuthDatabase()
db.change_password('admin', 'admin123', 'new_secure_password_here')
```

#### Update JWT Secret
```python
# Edit auth.py line 13:
self.secret_key = os.environ.get('JWT_SECRET_KEY', 'your-new-secret-key-at-least-32-chars-long')
```

#### Environment Configuration
```bash
# Create .env file
JWT_SECRET_KEY=production-secret-key-min-32-characters-long-and-random
AUTH_DB_PATH=/var/data/auth.db
ANOMALY_DB_PATH=/var/data/anomaly_detection.db
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
SMTP_USER=alerts@company.com
SMTP_PASSWORD=your-email-password
LOG_LEVEL=INFO
```

### 2. Database Setup

#### Create Data Directory
```bash
mkdir -p /var/data/logs
mkdir -p /var/data/backups
chmod 700 /var/data
```

#### Initialize Databases
```bash
python3 << 'EOF'
from auth import AuthDatabase
from database import Database

# Initialize both databases
auth_db = AuthDatabase(db_path='/var/data/auth.db')
db = Database(db_path='/var/data/anomaly_detection.db')

# Create admin user with strong password
auth_db.create_user('admin', 'your_secure_password_here', 'admin@company.com', 'admin')

print("✓ Databases initialized")
print("✓ Admin user created")
EOF
```

#### Backup Setup
```bash
# Create backup script: backup_databases.sh
#!/bin/bash
BACKUP_DIR="/var/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup auth database
cp /var/data/auth.db $BACKUP_DIR/auth_db_$DATE.db

# Backup anomaly database  
cp /var/data/anomaly_detection.db $BACKUP_DIR/anomaly_db_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup_databases.sh >> /var/log/backup.log 2>&1
```

### 3. Logging & Monitoring

#### Configure Logging
```python
# Create logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': '/var/log/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'WARNING',
            'formatter': 'detailed',
            'filename': '/var/log/security.log',
            'maxBytes': 10485760,
            'backupCount': 10,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file', 'security'],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### 4. SSL/HTTPS Setup

#### Generate Self-Signed Certificate (Testing)
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out /etc/ssl/certs/server.crt -keyout /etc/ssl/private/server.key -days 365
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/anomaly-detection
server {
    listen 443 ssl http2;
    server_name anomaly.company.com;
    
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    location / {
        limit_req zone=api burst=20;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /auth/login {
        limit_req zone=login burst=2;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
    
    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 80;
    server_name anomaly.company.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Phase 2: Application Deployment

### 1. Deploy Application

#### Create Systemd Service
```ini
# /etc/systemd/system/anomaly-api.service
[Unit]
Description=AI Login Anomaly Detection API
After=network.target

[Service]
Type=notify
User=app
WorkingDirectory=/opt/anomaly-detection
Environment="JWT_SECRET_KEY=your-secret-key"
Environment="AUTH_DB_PATH=/var/data/auth.db"
Environment="ANOMALY_DB_PATH=/var/data/anomaly_detection.db"
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable anomaly-api
sudo systemctl start anomaly-api
sudo systemctl status anomaly-api
```

### 2. Deploy Dashboard

#### Streamlit Service
```ini
# /etc/systemd/system/anomaly-dashboard.service
[Unit]
Description=AI Login Anomaly Detection Dashboard
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/anomaly-detection
ExecStart=/usr/bin/streamlit run app.py --server.port 8501 --logger.level=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
sudo systemctl enable anomaly-dashboard
sudo systemctl start anomaly-dashboard
```

### 3. Docker Deployment (Alternative)

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - ./logs:/var/log
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      AUTH_DB_PATH: /data/auth.db
      ANOMALY_DB_PATH: /data/anomaly_detection.db
    restart: always

  dashboard:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/data
    command: streamlit run app.py
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    restart: always

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/ssl:/etc/ssl:ro
    depends_on:
      - api
      - dashboard
    restart: always
```

---

## Phase 3: Post-Deployment

### 1. Verification

#### Health Check
```bash
curl -X GET https://anomaly.company.com/health
```

#### Test Authentication
```bash
# Get token
TOKEN=$(curl -s -X POST https://anomaly.company.com/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your_new_password"}' | jq -r '.token')

# Test API
curl -X GET https://anomaly.company.com/api/v1/threats \
  -H "Authorization: Bearer $TOKEN"
```

#### Check Logs
```bash
sudo journalctl -u anomaly-api -f
sudo tail -f /var/log/app.log
```

### 2. Monitoring Setup

#### Prometheus Metrics
```python
# Add to api.py
from prometheus_client import Counter, Histogram, start_http_server

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

# Start metrics server
start_http_server(8001)
```

#### Alert Rules (Prometheus)
```yaml
# alerts.yml
groups:
  - name: anomaly_detection
    rules:
      - alert: APIDown
        expr: up{job="anomaly-api"} == 0
        for: 5m
        annotations:
          summary: "API is down"
      
      - alert: HighErrorRate
        expr: rate(requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighAnomalyRate
        expr: rate(predictions_anomaly[5m]) > 0.2
        for: 10m
        annotations:
          summary: "Anomaly rate above threshold"
```

### 3. Backup Verification

#### Test Restore
```bash
# Stop services
sudo systemctl stop anomaly-api anomaly-dashboard

# Restore from backup
cp /var/data/backups/auth_db_*.db /var/data/auth.db
cp /var/data/backups/anomaly_db_*.db /var/data/anomaly_detection.db

# Restart
sudo systemctl start anomaly-api anomaly-dashboard

# Verify
curl -X GET https://anomaly.company.com/health
```

---

## Phase 4: Ongoing Operations

### 1. Daily Tasks
- ✓ Monitor application logs
- ✓ Check system resources (CPU, memory, disk)
- ✓ Verify backup completion
- ✓ Review alert logs

### 2. Weekly Tasks
- ✓ Review anomaly detection accuracy
- ✓ Analyze false positive/negative rates
- ✓ Check user activity reports
- ✓ Validate data retention policies

### 3. Monthly Tasks
- ✓ Security audit
- ✓ Update threat intelligence rules
- ✓ Review user roles/permissions
- ✓ Database optimization
- ✓ Capacity planning

### 4. Quarterly Tasks
- ✓ Model retraining
- ✓ Security patches
- ✓ Disaster recovery drill
- ✓ Performance optimization

---

## Troubleshooting

### API Won't Start
```bash
# Check port
sudo netstat -tlnp | grep 8000

# Check logs
sudo journalctl -u anomaly-api -n 50

# Run manually for debugging
python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Database Locked
```bash
# Check locks
lsof | grep auth.db

# Restart services
sudo systemctl restart anomaly-api
```

### High Memory Usage
```bash
# Monitor
free -h
ps aux | grep python

# Restart service (will auto-restart)
sudo systemctl restart anomaly-api
```

### SSL Certificate Issues
```bash
# Check expiration
openssl x509 -enddate -noout -in /etc/ssl/certs/server.crt

# Renew with Let's Encrypt
sudo certbot renew
```

---

## Scaling Considerations

### Stage 1: Current (100 users)
- Single server
- SQLite databases
- Single API instance
- Nginx reverse proxy

### Stage 2: Growth (1000 users)
- Multiple API instances (load balanced)
- PostgreSQL for databases
- Redis caching layer
- Dedicated logging server

### Stage 3: Enterprise (10000+ users)
- Kubernetes deployment
- Multiple regions
- Database replication
- Message queue (RabbitMQ)
- Distributed caching (Redis cluster)

---

## Security Checklist

- [ ] Change default admin password
- [ ] Update JWT secret key
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Create incident response plan
- [ ] Document disaster recovery
- [ ] Regular security audits
- [ ] Keep dependencies updated

---

## Support & Escalation

### Tier 1: Application Issues
- Check logs: `/var/log/app.log`
- Restart service: `systemctl restart anomaly-api`
- Review recent changes

### Tier 2: Database Issues  
- Check connections: `lsof | grep .db`
- Verify disk space: `df -h`
- Restore from backup if needed

### Tier 3: Infrastructure Issues
- CPU/memory alerts
- Network connectivity
- Storage capacity
- Disaster recovery

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop current version
sudo systemctl stop anomaly-api anomaly-dashboard

# 2. Restore previous code
git checkout previous-tag
# OR restore from backup
cp /var/backups/app_*.tar.gz /opt/
tar -xzf /opt/app_*.tar.gz -C /opt/

# 3. Restore databases from backup
cp /var/data/backups/auth_db_*.db /var/data/auth.db
cp /var/data/backups/anomaly_db_*.db /var/data/anomaly_detection.db

# 4. Start services
sudo systemctl start anomaly-api anomaly-dashboard

# 5. Verify
curl https://anomaly.company.com/health
```

---

## Contact & Escalation

- **On-call Engineer:** [contact info]
- **Security Team:** [contact info]
- **Database Admin:** [contact info]
- **Infrastructure Team:** [contact info]

---

**Deployment Status:** Ready for production  
**Last Updated:** 2024  
**Version:** 1.0.0

🚀 **You're ready to deploy!**
