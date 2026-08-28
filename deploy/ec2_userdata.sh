#!/usr/bin/env bash
# EC2 user-data bootstrap script — runs on first boot as root
# Installs Docker, clones repo, builds image, starts service
set -e

exec > /var/log/sampati-boot.log 2>&1

echo "=== SAMPATI EC2 Bootstrap ==="
dnf update -y
dnf install -y docker git nginx

# Start Docker
systemctl enable docker
systemctl start docker

# ── Clone the repo ──────────────────────────────────────────────────────────
cd /opt
git clone https://github.com/404Avinash/SAMPATI_V2.git sampati
cd sampati

# ── Build and start with Docker ─────────────────────────────────────────────
docker build -t sampati:latest .
docker run -d \
  --name sampati \
  --restart unless-stopped \
  -p 8000:8000 \
  sampati:latest

# ── Configure nginx as reverse proxy ───────────────────────────────────────
cat > /etc/nginx/conf.d/sampati.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # API and WebSocket
    location /upi/ {
        proxy_pass         http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location /gateway/  { proxy_pass http://localhost:8000; proxy_set_header Host $host; }
    location /cases/    { proxy_pass http://localhost:8000; proxy_set_header Host $host; }
    location /docs      { proxy_pass http://localhost:8000; proxy_set_header Host $host; }
    location /openapi.json { proxy_pass http://localhost:8000; proxy_set_header Host $host; }
    location /health    { proxy_pass http://localhost:8000; proxy_set_header Host $host; }
    location /ws/       { proxy_pass http://localhost:8000; proxy_http_version 1.1;
                          proxy_set_header Upgrade $http_upgrade;
                          proxy_set_header Connection "upgrade"; }

    # Serve React frontend
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
EOF

systemctl enable nginx
systemctl restart nginx

echo "=== Bootstrap complete ==="
echo "SAMPATI is running at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
