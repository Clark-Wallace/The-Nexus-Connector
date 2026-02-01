# Production Deployment Guide

This guide covers deploying the UAP Framework in production environments with high availability, scalability, and security considerations.

## Overview

The UAP Framework supports multiple deployment patterns depending on your requirements:

- **Single Machine**: Simple deployment for small-scale applications
- **Distributed**: Multi-machine deployment for scalability
- **Cloud-Native**: Kubernetes-based deployment for cloud environments
- **Hybrid**: Combination of on-premises and cloud resources

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- Network: 100 Mbps

**Recommended for Production:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+ SSD
- Network: 1 Gbps+

### Software Dependencies

```bash
# Python 3.8+
python3 --version

# Redis (for distributed deployments)
redis-server --version

# PostgreSQL (for persistent storage)
psql --version

# Docker (for containerized deployments)
docker --version

# Kubernetes (for cloud-native deployments)
kubectl version
```

## Single Machine Deployment

### Installation

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash uap
sudo usermod -aG sudo uap

# Switch to UAP user
sudo su - uap

# Install UAP Framework
pip install uap-framework

# Or install from source
git clone https://github.com/your-org/uap-framework.git
cd uap-framework
pip install -e .
```

### Configuration

Create production configuration file:

```yaml
# /etc/uap/config.yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

database:
  url: "postgresql://uap:password@localhost:5432/uap_prod"
  pool_size: 20
  max_overflow: 30

redis:
  url: "redis://localhost:6379/0"
  max_connections: 100

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/uap/uap.log"
  max_size: "100MB"
  backup_count: 10

security:
  secret_key: "your-secret-key-here"
  jwt_expiry: 3600
  rate_limit: 1000

monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30

agents:
  timeout: 300
  max_concurrent: 100
  retry_attempts: 3
```

### Service Configuration

Create systemd service:

```ini
# /etc/systemd/system/uap.service
[Unit]
Description=UAP Framework Service
After=network.target postgresql.service redis.service

[Service]
Type=forking
User=uap
Group=uap
WorkingDirectory=/home/uap/uap-framework
Environment=UAP_CONFIG=/etc/uap/config.yaml
ExecStart=/home/uap/.local/bin/uap-server start
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/home/uap/.local/bin/uap-server stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Database Setup

```bash
# Create database
sudo -u postgres createdb uap_prod
sudo -u postgres createuser uap

# Set password
sudo -u postgres psql -c "ALTER USER uap PASSWORD 'password';"

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE uap_prod TO uap;"

# Initialize schema
uap-admin db init
uap-admin db migrate
```

### Start Services

```bash
# Enable and start services
sudo systemctl enable uap
sudo systemctl start uap

# Check status
sudo systemctl status uap

# View logs
sudo journalctl -u uap -f
```

## Distributed Deployment

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   UAP Gateway   │    │  UAP Workers    │
│    (nginx)      │───▶│   (API Server)  │───▶│  (Task Exec)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │     Redis       │    │   PostgreSQL    │
│   (Grafana)     │    │   (Message      │    │   (Metadata)    │
│                 │    │    Queue)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Load Balancer Configuration

```nginx
# /etc/nginx/sites-available/uap
upstream uap_backend {
    least_conn;
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name uap.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name uap.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/uap.crt;
    ssl_certificate_key /etc/ssl/private/uap.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://uap_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://uap_backend/health;
        access_log off;
    }
    
    location /metrics {
        proxy_pass http://uap_backend/metrics;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

### Redis Cluster Setup

```bash
# Install Redis on multiple nodes
sudo apt-get install redis-server

# Configure Redis cluster
# Node 1 (10.0.1.20)
redis-cli --cluster create \
  10.0.1.20:7000 10.0.1.20:7001 \
  10.0.1.21:7000 10.0.1.21:7001 \
  10.0.1.22:7000 10.0.1.22:7001 \
  --cluster-replicas 1
```

### Database Replication

```sql
-- Master database configuration
-- postgresql.conf
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3
synchronous_commit = on

-- pg_hba.conf
host replication replicator 10.0.1.0/24 md5

-- Create replication user
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'password';
```

### Worker Node Configuration

```yaml
# worker-config.yaml
worker:
  node_id: "worker-01"
  role: "executor"
  max_tasks: 50

registry:
  type: "redis"
  url: "redis://10.0.1.20:7000,10.0.1.21:7000,10.0.1.22:7000"
  cluster: true

database:
  url: "postgresql://uap:password@10.0.1.30:5432/uap_prod"
  read_replicas:
    - "postgresql://uap:password@10.0.1.31:5432/uap_prod"
    - "postgresql://uap:password@10.0.1.32:5432/uap_prod"

monitoring:
  enabled: true
  node_exporter: true
  metrics_endpoint: "http://10.0.1.40:9090"
```

## Cloud-Native Deployment (Kubernetes)

### Namespace and RBAC

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: uap-system

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: uap-service-account
  namespace: uap-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: uap-cluster-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: uap-cluster-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: uap-cluster-role
subjects:
- kind: ServiceAccount
  name: uap-service-account
  namespace: uap-system
```

### ConfigMap and Secrets

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: uap-config
  namespace: uap-system
data:
  config.yaml: |
    server:
      host: "0.0.0.0"
      port: 8000
    redis:
      url: "redis://redis-service:6379/0"
    database:
      url: "postgresql://uap:password@postgres-service:5432/uap_prod"
    monitoring:
      enabled: true

---
apiVersion: v1
kind: Secret
metadata:
  name: uap-secrets
  namespace: uap-system
type: Opaque
data:
  database-password: cGFzc3dvcmQ=  # base64 encoded
  jwt-secret: eW91ci1qd3Qtc2VjcmV0  # base64 encoded
  api-keys: |
    openai_api_key: sk-...
    anthropic_api_key: sk-ant-...
```

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uap-api
  namespace: uap-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: uap-api
  template:
    metadata:
      labels:
        app: uap-api
    spec:
      serviceAccountName: uap-service-account
      containers:
      - name: uap-api
        image: uap-framework:latest
        ports:
        - containerPort: 8000
        - containerPort: 9090  # metrics
        env:
        - name: UAP_CONFIG
          value: "/etc/uap/config.yaml"
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: uap-secrets
              key: database-password
        volumeMounts:
        - name: config-volume
          mountPath: /etc/uap
        - name: secrets-volume
          mountPath: /etc/secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: uap-config
      - name: secrets-volume
        secret:
          secretName: uap-secrets

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uap-worker
  namespace: uap-system
spec:
  replicas: 5
  selector:
    matchLabels:
      app: uap-worker
  template:
    metadata:
      labels:
        app: uap-worker
    spec:
      containers:
      - name: uap-worker
        image: uap-framework:latest
        command: ["uap-worker"]
        env:
        - name: UAP_CONFIG
          value: "/etc/uap/config.yaml"
        - name: WORKER_TYPE
          value: "executor"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/uap
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "4000m"
      volumes:
      - name: config-volume
        configMap:
          name: uap-config
```

### Services

```yaml
# services.yaml
apiVersion: v1
kind: Service
metadata:
  name: uap-api-service
  namespace: uap-system
spec:
  selector:
    app: uap-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: uap-api-external
  namespace: uap-system
spec:
  selector:
    app: uap-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: uap-ingress
  namespace: uap-system
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - uap.yourdomain.com
    secretName: uap-tls
  rules:
  - host: uap.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: uap-api-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: uap-api-hpa
  namespace: uap-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: uap-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: uap-worker-hpa
  namespace: uap-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: uap-worker
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
- job_name: 'uap-api'
  static_configs:
  - targets: ['uap-api-service:9090']
  metrics_path: /metrics
  scrape_interval: 10s

- job_name: 'uap-workers'
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names:
      - uap-system
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: keep
    regex: uap-worker
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "UAP Framework Monitoring",
    "panels": [
      {
        "title": "Task Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(uap_tasks_completed_total[5m])",
            "legendFormat": "Tasks/sec"
          }
        ]
      },
      {
        "title": "Agent Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "uap_agent_response_time_seconds",
            "legendFormat": "{{agent_id}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(uap_tasks_failed_total[5m]) / rate(uap_tasks_total[5m]) * 100",
            "legendFormat": "Error %"
          }
        ]
      }
    ]
  }
}
```

## Security Hardening

### SSL/TLS Configuration

```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/uap.key \
  -out /etc/ssl/certs/uap.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=uap.yourdomain.com"

# Set proper permissions
chmod 600 /etc/ssl/private/uap.key
chmod 644 /etc/ssl/certs/uap.crt
```

### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow UAP API (internal)
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Allow Redis (internal)
sudo ufw allow from 10.0.0.0/8 to any port 6379

# Allow PostgreSQL (internal)
sudo ufw allow from 10.0.0.0/8 to any port 5432

# Enable firewall
sudo ufw enable
```

### Environment Variables

```bash
# /etc/environment
UAP_SECRET_KEY="your-very-secure-secret-key"
UAP_DATABASE_PASSWORD="secure-database-password"
UAP_REDIS_PASSWORD="secure-redis-password"
UAP_JWT_SECRET="jwt-signing-secret"
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/var/backups/uap"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="uap_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h localhost -U uap uap_prod > $BACKUP_DIR/$BACKUP_FILE

# Compress backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/${BACKUP_FILE}.gz"
```

### Redis Backup

```bash
#!/bin/bash
# backup-redis.sh

BACKUP_DIR="/var/backups/uap/redis"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Save Redis data
redis-cli BGSAVE

# Wait for background save to complete
while [ $(redis-cli LASTSAVE) -eq $(redis-cli LASTSAVE) ]; do
  sleep 1
done

# Copy RDB file
cp /var/lib/redis/dump.rdb $BACKUP_DIR/dump_${DATE}.rdb

# Compress
gzip $BACKUP_DIR/dump_${DATE}.rdb

echo "Redis backup completed: $BACKUP_DIR/dump_${DATE}.rdb.gz"
```

### Automated Backup

```bash
# Add to crontab
crontab -e

# Daily database backup at 2 AM
0 2 * * * /usr/local/bin/backup-database.sh

# Daily Redis backup at 3 AM
0 3 * * * /usr/local/bin/backup-redis.sh
```

## Performance Tuning

### Database Optimization

```sql
-- PostgreSQL configuration
-- postgresql.conf

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Connection settings
max_connections = 200
```

### Redis Optimization

```conf
# redis.conf

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
tcp-keepalive 300
timeout 0

# Performance
tcp-backlog 511
```

### Application Tuning

```yaml
# Performance configuration
performance:
  worker_processes: 8
  max_connections: 1000
  connection_pool_size: 20
  task_queue_size: 10000
  batch_size: 100
  
cache:
  enabled: true
  ttl: 3600
  max_size: 1000
  
rate_limiting:
  enabled: true
  requests_per_minute: 1000
  burst_size: 100
```

## Troubleshooting

### Common Issues

**High Memory Usage:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Optimize garbage collection
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

**Database Connection Issues:**
```bash
# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"
```

**Redis Connection Issues:**
```bash
# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor

# Check memory usage
redis-cli info memory
```

### Log Analysis

```bash
# View UAP logs
tail -f /var/log/uap/uap.log

# Search for errors
grep -i error /var/log/uap/uap.log

# Analyze performance
grep "duration" /var/log/uap/uap.log | awk '{print $NF}' | sort -n
```

This production deployment guide provides comprehensive coverage of deploying the UAP Framework in various production environments with proper security, monitoring, and performance considerations.

