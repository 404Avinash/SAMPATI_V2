#!/usr/bin/env bash
# EC2 user-data bootstrap script — runs on first boot as root
# Installs Docker, clones repo, configures RDS PostgreSQL persistence, builds image, starts service
set -e

exec > /var/log/sampati-boot.log 2>&1

echo "=== SAMPATI EC2 Bootstrap with AWS RDS PostgreSQL Persistence ==="
dnf update -y
dnf install -y docker git nginx

# Start Docker
systemctl enable docker
systemctl start docker

# ── Clone the repo ──────────────────────────────────────────────────────────
if [ ! -d "/opt/sampati" ]; then
    cd /opt
    git clone https://github.com/404Avinash/SAMPATI_V2.git sampati
fi
cd /opt/sampati

# ── Environment & AWS RDS PostgreSQL Configuration ───────────────────────────
# Provisioning note for AWS RDS Free Tier (db.t3.micro):
# aws rds create-db-instance \
#     --db-instance-identifier sampati-db \
#     --db-instance-class db.t3.micro \
#     --engine postgres \
#     --engine-version 16.3 \
#     --master-username sampati_admin \
#     --master-user-password "StrongSecurePassword123" \
#     --allocated-storage 20 \
#     --storage-type gp2 \
#     --vpc-security-group-ids sg-xxxxxxxxx \
#     --db-name sampatidb \
#     --region ap-south-1

mkdir -p /opt/sampati
if [ ! -f "/opt/sampati/.env" ]; then
    cat << 'EOF' > /opt/sampati/.env
# AWS RDS PostgreSQL Connection URL (override with your RDS endpoint)
# Format: postgresql+asyncpg://<USER>:<PASSWORD>@<RDS_ENDPOINT>:5432/<DB_NAME>
DATABASE_URL=
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=30.0
FASTAPI_ENV=production
EOF
fi

# ── Build and start with Docker ─────────────────────────────────────────────
docker build -t sampati:latest .
docker rm -f sampati 2>/dev/null || true

# Run container passing the environment file for RDS persistence
docker run -d \
  --name sampati \
  --restart unless-stopped \
  --env-file /opt/sampati/.env \
  -p 8000:8000 \
  sampati:latest

# ── Configure nginx as reverse proxy ───────────────────────────────────────
# Clean base nginx.conf with WebSocket upgrade mapping
cat > /etc/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;

include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    include /etc/nginx/conf.d/*.conf;
}
EOF

cat > /etc/nginx/conf.d/sampati.conf << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    # Dedicated location for WebSocket streams
    location /ws/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }

    # API endpoints and Frontend SPA proxy
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection $connection_upgrade;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

# ── Install nightly restart systemd timer ────────────────────────────────────
if [ -f "/opt/sampati/deploy/sampati-nightly-restart.service" ]; then
    cp /opt/sampati/deploy/sampati-nightly-restart.service /etc/systemd/system/
    cp /opt/sampati/deploy/sampati-nightly-restart.timer /etc/systemd/system/
    chmod 644 /etc/systemd/system/sampati-nightly-restart.service /etc/systemd/system/sampati-nightly-restart.timer
    systemctl daemon-reload
    systemctl enable --now sampati-nightly-restart.timer
fi

# Make deploy helper scripts executable
chmod +x /opt/sampati/deploy/*.sh 2>/dev/null || true

systemctl enable nginx
systemctl restart nginx

# Retrieve public IPv4 (supporting both IMDSv1 and IMDSv2)
IMDS_TOKEN=$(curl -s -f -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || true)
if [ -n "$IMDS_TOKEN" ]; then
    PUBLIC_IP=$(curl -s -f -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
else
    PUBLIC_IP=$(curl -s -f http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
fi
PUBLIC_IP="${PUBLIC_IP:-localhost}"

echo "=== Bootstrap complete ==="
echo "SAMPATI V2 is running at http://${PUBLIC_IP}"
