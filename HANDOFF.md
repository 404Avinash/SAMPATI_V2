# SAMPATI V2 — Operations & Handoff Runbook

## 1. Project Overview

**SAMPATI V2** is a real-time Unified Payments Interface (UPI) mule-network interception and financial cybercrime intelligence platform. It provides:
- **Inline Risk Gateway**: Sub-10ms graph-based fraud scoring for live UPI transactions.
- **Mule-Ring Detection**: Federated cycle and layering pattern identification across PSP accounts.
- **Automated SAR Generation**: Suspicious Activity Report (SAR) compilation with visual graph forensic snapshots.
- **DPIP Feedback Integration**: Bidirectional synchronization with the Digital Payment Intelligence Platform.
- **Forensic Dashboard**: Interactive React/Vite single-page application (SPA) with live WebSocket threat streaming.

The platform is containerized using Docker and deployed on an AWS EC2 instance (`t3.micro`, Amazon Linux 2023) fronted by Nginx reverse proxy with automated maintenance and monitoring.

---

## 2. Architecture & Service Topology

```
                  +----------------------------------------------+
                  |               AWS EC2 Instance               |
                  |                (t3.micro / AL2023)           |
                  |                                              |
Internet (Port 80)|  +----------------------------------------+  |
----------------->|->|               Nginx                    |  |
                  |  |  - Proxy / -> localhost:8000 (SPA)     |  |
                  |  |  - Proxy /upi/*, /gateway/*, /cases/*  |  |
                  |  |  - Proxy /health, /docs, /openapi.json |  |
                  |  |  - Proxy /ws/* (WebSocket upgrade)     |  |
                  |  +----------------------------------------+  |
                  |                       |                      |
                  |                       v                      |
                  |  +----------------------------------------+  |
                  |  |      Docker: 'sampati' (Port 8000)     |  |
                  |  |  - FastAPI Backend (Uvicorn)           |  |
                  |  |  - Embedded React UI static bundle     |  |
                  |  +----------------------------------------+  |
                  |                                              |
                  |  +----------------------------------------+  |
                  |  | systemd timer:                         |  |
                  |  |   sampati-nightly-restart.timer        |  |
                  |  |   (Fires nightly at 20:30 UTC/02:00IST)|  |
                  |  +----------------------------------------+  |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         AWS CloudWatch (us-east-1)           |
                  |  - EstimatedCharges > $15 USD Alarm          |
                  |  - SNS Topic -> Email Notification           |
                  +----------------------------------------------+
```

---

## 3. Deployment Guide

### Prerequisites
1. **AWS CLI** installed and configured (`aws configure`) with an IAM user or role with permissions:
   - `AmazonEC2FullAccess`
   - `AmazonSSMReadOnlyAccess` (to resolve AMI)
   - `CloudWatchFullAccess`
   - `AmazonSNSFullAccess`
2. **EC2 Key Pair**: An existing key pair in region `ap-south-1` (default: `sampati-key`).
3. **Billing Region**: Billing alarms are published by AWS exclusively in `us-east-1` (handled automatically by scripts).

---

### Deploying the Platform (One-Command Deployment)

#### Option A: Linux / macOS / WSL (Bash)
```bash
# 1. Clone repository locally if not already present
git clone https://github.com/404Avinash/SAMPATI_V2.git
cd SAMPATI_V2

# 2. Make deployment script executable and run with your alert email
chmod +x deploy/aws_deploy.sh
ALERT_EMAIL="your-email@example.com" ./deploy/aws_deploy.sh
```

#### Option B: Windows (PowerShell)
```powershell
# 1. Navigate to repository root
cd SAMPATI_V2

# 2. Run PowerShell deployment script
powershell -ExecutionPolicy Bypass -File deploy\aws_deploy.ps1 -AlertEmail "your-email@example.com"
```

---

### What the Bootstrap Script (`deploy/ec2_userdata.sh`) Does Automatically
When EC2 boots:
1. Installs `docker`, `git`, and `nginx` via `dnf`.
2. Enables and starts the Docker daemon.
3. Clones the repository to `/opt/sampati`.
4. Builds the container image `sampati:latest` and runs container `sampati` with `--restart unless-stopped -p 8000:8000`.
5. Configures Nginx reverse proxy with WebSocket upgrade support.
6. Installs `deploy/sampati-nightly-restart.service` and `deploy/sampati-nightly-restart.timer` to `/etc/systemd/system/`.
7. Reloads systemd daemon and arms the nightly restart timer (`systemctl enable --now sampati-nightly-restart.timer`).
8. Enables and restarts Nginx.

---

### Automated CI/CD Pipeline & GitHub Secrets Setup

SAMPATI V2 includes a fully automated GitHub Actions CI/CD workflow defined in `.github/workflows/deploy.yml`. On every push to the `main` branch:
1. **CI Stage (`test`)**: Spins up an ephemeral PostgreSQL 15 service container (`postgres:15-alpine`), waits for healthy database readiness, sets `DATABASE_URL`, and executes the complete Python E2E verification test suite.
2. **CD Stage (`deploy`)**: Executes only if the `test` stage passes (`needs: test`). Connects securely to the AWS EC2 instance over SSH, pulls the latest code from `main`, stops/removes the existing container, builds the new Docker image, and restarts the `sampati` container with production environment persistence (`/opt/sampati/.env`).

#### Required GitHub Repository Secrets

To enable automated SSH deployments from GitHub Actions to your EC2 instance, configure the following three repository secrets:

| Secret Name | Value Description | Example / Format |
| :--- | :--- | :--- |
| `EC2_HOST` | The public IPv4 address or public DNS hostname of your AWS EC2 instance. | `13.233.xxx.xxx` or `ec2-13-233-xxx-xxx.ap-south-1.compute.amazonaws.com` |
| `EC2_USERNAME` | The SSH username for logging into the EC2 instance (for Amazon Linux 2023, default is `ec2-user`). | `ec2-user` |
| `EC2_SSH_KEY` | The raw PEM private key matching the EC2 key pair (e.g. `sampati-key.pem`). Paste the entire file contents including header and footer. | `-----BEGIN RSA PRIVATE KEY-----`<br>`MIIEowIBAAKCAQEA0...`<br>`-----END RSA PRIVATE KEY-----` |

#### Step-by-Step Guide: Adding Secrets to GitHub

1. Open your repository on GitHub: `https://github.com/<owner>/SAMPATI_V2`.
2. Navigate to **Settings** (top navigation tab of the repository).
3. In the left sidebar, expand **Secrets and variables** and click **Actions**.
4. Click the green **New repository secret** button.
5. Add each of the 3 secrets:
   - **Secret 1**: Name = `EC2_HOST`, Secret = `<Your EC2 Public IP>` -> Click **Add secret**.
   - **Secret 2**: Name = `EC2_USERNAME`, Secret = `ec2-user` -> Click **Add secret**.
   - **Secret 3**: Name = `EC2_SSH_KEY`, Secret = `<Contents of your .pem private key>` -> Click **Add secret**.
6. Once configured, every push to the `main` branch automatically validates the code and deploys the latest version to EC2. You can also trigger the workflow manually from the **Actions** tab using the **Run workflow** button.

---

## 4. Application Endpoints & Access URLs

Replace `<PUBLIC_IP>` with the public IPv4 address printed at the end of the deployment script:

| Resource | URL Pattern | Description |
| :--- | :--- | :--- |
| **Forensic Web Dashboard** | `http://<PUBLIC_IP>/` | React UI for transaction graph monitoring & ring analysis |
| **Interactive API Docs** | `http://<PUBLIC_IP>/docs` | Swagger UI for executing and testing API endpoints |
| **OpenAPI Spec** | `http://<PUBLIC_IP>/openapi.json` | Raw OpenAPI 3.0 specification |
| **Health Check Probe** | `http://<PUBLIC_IP>/health` | Service health status (`{"status":"ok","service":"sampati-upi","version":"2.0.0"}`) |
| **UPI Interception API** | `http://<PUBLIC_IP>/upi/` | Transaction scoring and mule intelligence endpoints |
| **Cases & SAR API** | `http://<PUBLIC_IP>/cases/` | Case management, audit trail, and SAR export |
| **Synthetic Data API** | `http://<PUBLIC_IP>/synthetic/` | Generator for testing mule networks |
| **WebSocket Threat Stream** | `ws://<PUBLIC_IP>/ws/` | Real-time event stream for frontend graph updates |

---

## 5. Operational Runbook

### 5.1. Checking Logs

Connect to the EC2 instance via SSH:
```bash
ssh -i ~/.ssh/sampati-key.pem ec2-user@<PUBLIC_IP>
```

#### Application & Container Logs:
```bash
# Follow real-time application logs inside Docker
docker logs -f sampati

# Tail last 200 log lines with timestamps
docker logs -n 200 -t sampati
```

#### EC2 Boot & Bootstrap Logs:
```bash
# View complete first-boot userdata bootstrap log
sudo cat /var/log/sampati-boot.log

# Follow boot log during initial provisioning
sudo tail -f /var/log/sampati-boot.log
```

#### Nginx Reverse Proxy Logs:
```bash
# Nginx error log
sudo tail -f /var/log/nginx/error.log

# Nginx access log
sudo tail -f /var/log/nginx/access.log
```

#### Systemd Timer & Service Logs:
```bash
# Check execution logs for the nightly restart service
sudo journalctl -u sampati-nightly-restart.service -n 50 --no-pager
```

---

### 5.2. Restarting the Container & Services

#### Manual Container Restart:
```bash
# Restart the container immediately
docker restart sampati

# Check container state
docker ps --filter "name=sampati"
```

#### Rebuilding Container After Code Changes:
```bash
cd /opt/sampati
git pull origin main
docker build -t sampati:latest .
docker stop sampati && docker rm sampati
docker run -d --name sampati --restart unless-stopped -p 8000:8000 sampati:latest
```

#### Restarting Nginx:
```bash
# Test nginx configuration syntax
sudo nginx -t

# Restart nginx service
sudo systemctl restart nginx
```

---

### 5.3. AWS Billing Alarm ($15 Threshold)

AWS CloudWatch Billing metrics are published in region `us-east-1`. The alarm alerts the operator when `EstimatedCharges` exceeds $15 USD.

#### Standalone Setup via Bash:
```bash
# Run with email parameter
./deploy/billing_alarm.sh operator@yourdomain.com
```

#### Standalone Setup via PowerShell:
```powershell
powershell -File deploy\billing_alarm.ps1 -AlertEmail "operator@yourdomain.com"
```

#### Required Action After Setup:
AWS SNS sends an email with the subject:
`AWS Notification - Subscription Confirmation`
> **Important**: The recipient **must click the "Confirm subscription" link** inside the email to start receiving alert notifications.

#### Alarm Configuration Summary:
- **Metric**: `EstimatedCharges`
- **Namespace**: `AWS/Billing`
- **Dimension**: `Currency=USD`
- **Statistic**: `Maximum`
- **Period**: `21600` seconds (6 hours)
- **Threshold**: `> 15.00`
- **Region**: `us-east-1`
- **Action**: SNS Topic `arn:aws:sns:us-east-1:<account-id>:sampati-billing-alerts`

---

### 5.4. Nightly Container Restart Timer

To prevent memory fragmentation and ensure long-term stability, a systemd timer restarts the `sampati` container every night at **02:00 IST (20:30 UTC)**.

#### Timer Files:
- `/etc/systemd/system/sampati-nightly-restart.service`
- `/etc/systemd/system/sampati-nightly-restart.timer`

#### Inspecting Timer Status & Next Trigger Time:
```bash
# View active timers and next scheduled trigger
systemctl list-timers sampati-nightly-restart.timer

# View timer unit status
sudo systemctl status sampati-nightly-restart.timer
```

#### Manually Triggering the Restart Unit (For Testing):
```bash
# Trigger the oneshot restart service directly
sudo systemctl start sampati-nightly-restart.service

# Check execution logs
sudo journalctl -u sampati-nightly-restart.service -e
```

---

### 5.5. Reboot-Survival Verification

A dedicated verification script is included in `deploy/verify_reboot.sh` to test complete self-healing after instance reboot.

#### To Execute Verification:
```bash
# On the EC2 instance:
sudo /opt/sampati/deploy/verify_reboot.sh
```

#### What It Validates:
1. `Docker daemon` is active and running (`systemctl is-active docker`).
2. `sampati` container exists and is in `running` state (`docker inspect`).
3. `nginx` reverse proxy is active (`systemctl is-active nginx`).
4. `/health` endpoint returns `HTTP 200` through Nginx (`curl http://127.0.0.1/health`).

#### Sample Success Output:
```
========================================================
   SAMPATI V2 Post-Reboot Verification Suite
========================================================

Checking Docker daemon status ... [PASS]
  -> Docker daemon is active and responding.
Checking 'sampati' container state ... [PASS]
  -> Container 'sampati' is in running state (Status: running).
Checking nginx service status ... [PASS]
  -> nginx service is active and running.
Checking /health endpoint via nginx reverse proxy ... [PASS]
  -> HTTP 200 OK received from http://127.0.0.1/health.
     Payload: {"status":"ok","service":"sampati-upi","version":"2.0.0"}
Checking nightly restart timer status ... [PASS]
  -> sampati-nightly-restart.timer is active and armed.

========================================================
Verification Summary: 4 passed, 0 failed
========================================================
Result: ALL REBOOT SURVIVAL CHECKS PASSED [OK]
```

---

## 6. Troubleshooting & Diagnostics

| Symptom | Probable Cause | Diagnostic Command & Resolution |
| :--- | :--- | :--- |
| **HTTP 502 Bad Gateway** | Container `sampati` is stopped or initializing | Run `docker ps -a` to check if container crashed. Inspect logs: `docker logs sampati`. If stopped, run `docker start sampati`. |
| **Cannot reach http://`<PUBLIC_IP>`** | Security Group missing Port 80 ingress | Verify Security Group ingress rules in AWS console or CLI: `aws ec2 describe-security-groups --group-names sampati-sg`. Ensure TCP port 80 and 22 are open. |
| **Health check fails (000/timeout)** | Nginx or Docker container not listening | Check nginx status: `sudo systemctl status nginx`. Test direct container response: `curl -v http://localhost:8000/health`. |
| **Timer not firing** | Timer unit not enabled | Run `sudo systemctl enable --now sampati-nightly-restart.timer`. Check next execution with `systemctl list-timers`. |
| **Billing alarm in INSUFFICIENT_DATA** | Normal for new AWS accounts (takes 6-24h) | AWS Billing metrics publish once every few hours. Check metric status in AWS CloudWatch Console (`us-east-1`). |
