#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SAMPATI AWS Deployment Script
# Uses: EC2 t3.micro (Free Tier) + Docker + nginx
# Cost: ~$0/month on free tier, ~$8/month after 12 months
#
# Prerequisites:
#   - AWS CLI installed and configured (aws configure)
#   - A key pair created in your region (update KEY_NAME below)
#   - Docker Hub account (optional — can also build on EC2)
#
# Usage:
#   chmod +x deploy/aws_deploy.sh
#   ./deploy/aws_deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ── CONFIG — edit these ──────────────────────────────────────────────────────
AWS_REGION="ap-south-1"       # Mumbai (closest to India)
KEY_NAME="sampati-key"        # Name of your EC2 key pair
INSTANCE_TYPE="t3.micro"      # Free tier eligible
SECURITY_GROUP="sampati-sg"
INSTANCE_NAME="sampati-upi"
ALERT_EMAIL="${1:-${ALERT_EMAIL:-"operator@example.com"}}" # Email for AWS billing alarms ($15 threshold)

echo "=== SAMPATI AWS Deployment ==="

# ── 0. Resolve latest Amazon Linux 2023 AMI for region ──────────────────────
echo "Resolving latest Amazon Linux 2023 AMI..."
AMI_ID=$(aws ssm get-parameters \
  --names "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64" \
  --region "$AWS_REGION" \
  --query "Parameters[0].Value" \
  --output text 2>/dev/null || true)

if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
  AMI_ID="ami-0f58b397bc5c1f2e2" # Fallback Mumbai AL2023 AMI
fi
echo "  AMI: $AMI_ID"

# ── 1. Create Security Group ─────────────────────────────────────────────────
echo "Creating security group..."
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SECURITY_GROUP" \
  --query "SecurityGroups[0].GroupId" \
  --output text --region $AWS_REGION 2>/dev/null || true)

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
  SG_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP \
    --description "SAMPATI UPI Gateway" \
    --region $AWS_REGION \
    --query GroupId --output text)
  
  # Allow SSH, HTTP, HTTPS, and app port
  aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID --region $AWS_REGION \
    --ip-permissions \
    "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=0.0.0.0/0}]" \
    "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0}]" \
    "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0}]" \
    "IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges=[{CidrIp=0.0.0.0/0}]"
  
  echo "Security group created: $SG_ID"
else
  echo "Using existing security group: $SG_ID"
fi

# ── 2. Launch EC2 Instance ───────────────────────────────────────────────────
echo "Launching EC2 instance..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_DATA_PATH="$SCRIPT_DIR/ec2_userdata.sh"

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --region $AWS_REGION \
  --user-data "file://$USER_DATA_PATH" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
  --query "Instances[0].InstanceId" \
  --output text)

echo "Instance launched: $INSTANCE_ID"
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

# ── 3. Get Public IP ─────────────────────────────────────────────────────────
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

# ── 4. Set up CloudWatch Billing Alarm ($15 Threshold) ──────────────────────
echo ""
echo "Setting up AWS CloudWatch Billing Alarm ($15 threshold)..."
BILLING_REGION="us-east-1"
SNS_TOPIC_NAME="sampati-billing-alerts"
ALARM_NAME="sampati-billing-alarm-15usd"

if [ "$ALERT_EMAIL" != "operator@example.com" ] && [ -n "$ALERT_EMAIL" ]; then
  TOPIC_ARN=$(aws sns create-topic \
    --name "$SNS_TOPIC_NAME" \
    --region "$BILLING_REGION" \
    --query "TopicArn" \
    --output text 2>/dev/null || true)
  
  if [ -n "$TOPIC_ARN" ] && [ "$TOPIC_ARN" != "None" ]; then
    aws sns subscribe \
      --topic-arn "$TOPIC_ARN" \
      --protocol email \
      --notification-endpoint "$ALERT_EMAIL" \
      --region "$BILLING_REGION" >/dev/null

    aws cloudwatch put-metric-alarm \
      --alarm-name "$ALARM_NAME" \
      --alarm-description "Trigger alarm when AWS monthly estimated charges exceed \$15 USD" \
      --metric-name "EstimatedCharges" \
      --namespace "AWS/Billing" \
      --statistic "Maximum" \
      --period 21600 \
      --threshold 15 \
      --comparison-operator "GreaterThanThreshold" \
      --dimensions "Name=Currency,Value=USD" \
      --evaluation-periods 1 \
      --alarm-actions "$TOPIC_ARN" \
      --region "$BILLING_REGION"

    echo "  Billing alarm created for EstimatedCharges > \$15 USD ($ALERT_EMAIL)"
    echo "  [!] Please confirm the subscription email sent by AWS SNS to $ALERT_EMAIL."
  else
    echo "  [ERROR] Failed to create or retrieve SNS Topic ARN." >&2
  fi
else
  echo "  [INFO] Default ALERT_EMAIL detected. To configure the $15 billing alarm, run:"
  echo "         ./deploy/billing_alarm.sh your-email@domain.com"
fi

echo ""
echo "=== Deployment Complete ==="
echo "Instance ID : $INSTANCE_ID"
echo "Public IP   : $PUBLIC_IP"
echo ""
echo "Wait ~3-5 minutes for user-data script to finish, then:"
echo "  App URL  : http://$PUBLIC_IP"
echo "  API Docs : http://$PUBLIC_IP/docs"
echo "  SSH      : ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "To verify reboot resilience:"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/sampati/deploy/verify_reboot.sh'"
echo ""
echo "To check startup logs:"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'sudo journalctl -u docker -f'"

